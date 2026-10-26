"""Streamlit interface for the rental valuation and comparable-search tools."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from app.i18n import t


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from src.comps import SimilarFinder
from src.parsers import parse_rooms
from src.predict import valuate


DATA_DIR = PROJECT_ROOT / "data"
LISTINGS_PATH = DATA_DIR / "interim" / "listings_parsed_v7.csv"


def _stats_path() -> Path:
	for path in (
		DATA_DIR / "interim" / "municipality_stats.csv",
		DATA_DIR / "processed" / "municipality_stats.csv",
		DATA_DIR / "municipality_stats.csv",
	):
		if path.exists():
			return path
	return DATA_DIR / "interim" / "municipality_stats.csv"


@st.cache_resource
def load_finder() -> SimilarFinder:
	required = ["municipality", "area_m2", "age_years", "walk_min_nearest", "stories_above", "n_rooms", "Price_yen"]
	header = pd.read_csv(LISTINGS_PATH, nrows=0)
	missing = [column for column in required if column not in header.columns]
	if missing:
		raise KeyError(f"Missing required column(s) in CSV: {missing}")
	return SimilarFinder(pd.read_csv(LISTINGS_PATH, usecols=required))


st.set_page_config(page_title="Tokyo Rental Intelligence", page_icon="🏠")
lang = st.radio(
	"Language",
	["en", "ja"],
	format_func=lambda x: "EN" if x == "en" else "日本語",
	horizontal=True,
	label_visibility="collapsed",
)
st.title(t(lang, "title"))

stats = pd.read_csv(_stats_path())
municipality_column = "municipality" if "municipality" in stats.columns else stats.columns[0]
municipalities = sorted(stats[municipality_column].dropna().astype(str).unique())

with st.sidebar:
	with st.form("valuation"):
		st.header(t(lang, "property_details"))
		municipality = st.selectbox(t(lang, "municipality"), municipalities)
		area_m2 = st.number_input(t(lang, "area_m2"), min_value=0.0, value=25.0, step=1.0)
		age_years = st.number_input(t(lang, "age_years"), min_value=0.0, value=10.0, step=1.0)
		walk_min_nearest = st.number_input(t(lang, "walk_min_nearest"), min_value=0.0, value=8.0, step=1.0)
		floor_min = st.number_input(t(lang, "floor_min"), min_value=0, value=2, step=1)
		stories_above = st.number_input(t(lang, "stories_above"), min_value=0, value=5, step=1)
		madori = st.selectbox(t(lang, "layout"), ["ワンルーム", "1K", "1DK", "1LDK", "2K", "2DK", "2LDK", "3LDK"])
		asking_rent = st.number_input(t(lang, "asking_rent"), min_value=0, value=0, step=5000)
		submit = st.form_submit_button(t(lang, "estimate_rent"), type="primary")

parsed = parse_rooms(madori)
room_names = ("n_rooms", "has_L", "has_D", "has_K", "has_S", "is_1R")
if parsed[0] == "FAILED":
	st.error(f"{t(lang, 'layout_parse_error')}: {madori}")
	st.stop()
room_features = dict(zip(room_names, parsed))

attrs = {
	"municipality": municipality,
	"area_m2": area_m2,
	"age_years": age_years,
	"walk_min_nearest": walk_min_nearest,
	"floor_min": floor_min,
	"stories_above": stories_above,
	**room_features,
}

if "result" not in st.session_state:
	st.session_state.result = None
	st.session_state.comparables = None

if submit:
	if area_m2 <= 0:
		st.error(t(lang, "area_positive"))
		st.stop()
	if stories_above < 1:
		st.error(t(lang, "stories_min"))
		st.stop()
	if floor_min > stories_above:
		st.error(t(lang, "floor_exceeds_stories"))
		st.stop()
	try:
		r = valuate(attrs, asking_rent or None)
		finder = load_finder()
		comparables = finder.find(attrs)
		st.session_state.result = r
		st.session_state.comparables = comparables
	except Exception as exc:
		st.error(f"{t(lang, 'error')}: {type(exc).__name__}: {exc}")

result = st.session_state.result
comparables = st.session_state.comparables
if result is not None:
	st.metric(t(lang, "estimated_monthly_rent"), f"¥{result['estimate']:,.0f}")
	st.write(f"{t(lang, 'interval_80')}: ¥{result['lo']:,.0f} – ¥{result['hi']:,.0f}")
	if "label" in result:
		position_key = {
			"above": "label_above",
			"within": "label_within",
			"below": "label_below",
		}.get(result["position"], result["position"])
		st.write(
			f"{t(lang, 'position')}: {t(lang, position_key)} | "
			f"{t(lang, 'gap')}: {result['gap_pct']:+.1%} | "
			f"{t(lang, 'label')}: {result['label']}"
		)
	if result["confidence"] == "low":
		st.warning(t(lang, "low_confidence"))

	if comparables is not None:
		st.write(f"{t(lang, 'comparable_range')}: ¥{comparables['p25']:,.0f} – ¥{comparables['p75']:,.0f}")
		st.write(f"{t(lang, 'comparable_median')}: ¥{comparables['median']:,.0f}")
		st.write(f"{t(lang, 'comparable_listings')}: {comparables['n']}")
		if comparables["p25"] > result["hi"] or comparables["p75"] < result["lo"]:
			st.info(t(lang, "comps_differ"))
	else:
		st.info(t(lang, "no_similar_listings"))
	st.caption(t(lang, "results_disclaimer"))
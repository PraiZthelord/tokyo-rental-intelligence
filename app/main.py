"""Streamlit interface for the rental valuation and comparable-search tools."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from app.i18n import t
from app.map_tab import render_map
from src.comps import SimilarFinder
from src.parsers import parse_rooms
from src.predict import valuate


DATA_DIR = PROJECT_ROOT / "data"
LISTINGS_PATH = DATA_DIR / "interim" / "listings_parsed_v7.csv"
LAYOUTS = ["ワンルーム", "1K", "1DK", "1LDK", "2K", "2DK", "2LDK", "3K", "3DK", "3LDK", "4LDK"]


def _stats_path() -> Path:
	for path in (
		DATA_DIR / "interim" / "municipality_stats.csv",
		DATA_DIR / "processed" / "municipality_stats.csv",
		DATA_DIR / "municipality_stats.csv",
		PROJECT_ROOT / "app" / "data" / "municipality_stats.csv",
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

from src.recommender import recommend


@st.cache_data
def load_valuation_table() -> pd.DataFrame:
	return pd.read_csv(PROJECT_ROOT / "data" / "interim" / "valuation_table.csv")


tabs = st.tabs([t(lang, "predictor"), t(lang, "recommender"), t(lang, "map")])
with tabs[0]:
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
	attrs = {"municipality": municipality, "area_m2": area_m2, "age_years": age_years, "walk_min_nearest": walk_min_nearest, "floor_min": floor_min, "stories_above": stories_above, **room_features}
	if "result" not in st.session_state:
		st.session_state.result = None
		st.session_state.comparables = None
	if submit:
		if area_m2 <= 0:
			st.error(t(lang, "area_positive")); st.stop()
		if stories_above < 1:
			st.error(t(lang, "stories_min")); st.stop()
		if floor_min > stories_above:
			st.error(t(lang, "floor_exceeds_stories")); st.stop()
		try:
			r = valuate(attrs, asking_rent or None)
			st.session_state.result = r
			if LISTINGS_PATH.exists():
				st.session_state.comparables = load_finder().find(attrs)
			else:
				st.session_state.comparables = None
		except Exception as exc:
			st.error(f"{t(lang, 'error')}: {type(exc).__name__}: {exc}")
	result = st.session_state.result
	comparables = st.session_state.comparables
	if result is not None:
		st.metric(t(lang, "estimated_monthly_rent"), f"¥{result['estimate']:,.0f}")
		st.write(f"{t(lang, 'interval_80')}: ¥{result['lo']:,.0f} – ¥{result['hi']:,.0f}")
		if "label" in result:
			position_key = {"above": "label_above", "within": "label_within", "below": "label_below"}.get(result["position"], result["position"])
			st.write(f"{t(lang, 'position')}: {t(lang, position_key)} | {t(lang, 'gap')}: {result['gap_pct']:+.1%} | {t(lang, 'label')}: {result['label']}")
		if result["confidence"] == "low":
			st.warning(t(lang, "low_confidence"))
		if comparables is not None:
			st.write(f"{t(lang, 'comparable_range')}: ¥{comparables['p25']:,.0f} – ¥{comparables['p75']:,.0f}")
			st.write(f"{t(lang, 'comparable_median')}: ¥{comparables['median']:,.0f}")
			st.write(f"{t(lang, 'comparable_listings')}: {comparables['n']}")
			if comparables["p25"] > result["hi"] or comparables["p75"] < result["lo"]:
				st.info(t(lang, "comps_differ"))
		else:
			if LISTINGS_PATH.exists():
				st.info(t(lang, "no_similar_listings"))
			else:
				st.info(t(lang, "comparables_unavailable"))
		st.caption(t(lang, "results_disclaimer"))

with tabs[1]:
	valuation_path = PROJECT_ROOT / "data" / "interim" / "valuation_table.csv"
	if not valuation_path.exists():
		st.info(t(lang, "recommender_unavailable"))
	else:
		val = load_valuation_table()
		def _column(*names):
			return next((name for name in names if name in val.columns), None)
		layout_col = _column("layout", "madori")
		municipality_col = _column("municipality")
		with st.form("recommender"):
			max_rent = st.number_input(t(lang, "max_rent"), min_value=0, value=0, step=5000)
			min_area = st.number_input(t(lang, "min_area"), min_value=0.0, value=0.0, step=1.0)
			layouts = st.multiselect(t(lang, "layouts"), LAYOUTS)
			municipality_options = sorted(val[municipality_col].dropna().astype(str).unique()) if municipality_col else []
			selected_municipalities = st.multiselect(t(lang, "municipalities"), municipality_options)
			max_walk = st.number_input(t(lang, "max_walk"), min_value=0.0, value=0.0, step=1.0)
			max_age = st.number_input(t(lang, "max_age"), min_value=0.0, value=0.0, step=1.0)
			value_weight = st.slider(t(lang, "weight_value"), 0.0, 1.0, 0.4, 0.05)
			walk_weight = st.slider(t(lang, "weight_walk"), 0.0, 1.0, 0.25, 0.05)
			age_weight = st.slider(t(lang, "weight_age"), 0.0, 1.0, 0.2, 0.05)
			area_weight = st.slider(t(lang, "weight_area"), 0.0, 1.0, 0.15, 0.05)
			recommend_submit = st.form_submit_button(t(lang, "recommend"), type="primary")
		if recommend_submit:
			weight_sum = value_weight + walk_weight + age_weight + area_weight
			if weight_sum == 0:
				st.error(t(lang, "weights_zero"))
			else:
				prefs = {}
				for key, value in (("max_rent", max_rent), ("min_area", min_area), ("max_walk", max_walk), ("max_age", max_age)):
					if value:
						prefs[key] = value
				if layouts: prefs["madori"] = layouts
				if selected_municipalities: prefs["municipalities"] = selected_municipalities
				weights = {"value": value_weight / weight_sum, "walk": walk_weight / weight_sum, "age": age_weight / weight_sum, "area": area_weight / weight_sum}
				result, note = recommend(val, prefs, weights)
				if result is None or len(result) == 0:
					st.info(note)
				else:
					st.dataframe(result)
					st.caption(note)

with tabs[2]:
	render_map(lang)
"""Streamlit interface for the rental valuation and comparable-search tools."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


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
st.title("Tokyo Rental Intelligence")

stats = pd.read_csv(_stats_path())
municipality_column = "municipality" if "municipality" in stats.columns else stats.columns[0]
municipalities = sorted(stats[municipality_column].dropna().astype(str).unique())

with st.sidebar:
	with st.form("valuation"):
		st.header("Property details")
		municipality = st.selectbox("Municipality", municipalities)
		area_m2 = st.number_input("Area (m²)", min_value=0.0, value=25.0, step=1.0)
		age_years = st.number_input("Age (years)", min_value=0.0, value=10.0, step=1.0)
		walk_min_nearest = st.number_input("Walk to nearest station (minutes)", min_value=0.0, value=8.0, step=1.0)
		floor_min = st.number_input("Floor", min_value=0, value=2, step=1)
		stories_above = st.number_input("Stories above", min_value=0, value=5, step=1)
		madori = st.selectbox("Layout", ["ワンルーム", "1K", "1DK", "1LDK", "2K", "2DK", "2LDK", "3LDK"])
		asking_rent = st.number_input("Asking rent (yen; 0 means none)", min_value=0, value=0, step=5000)
		submit = st.form_submit_button("Estimate rent", type="primary")

parsed = parse_rooms(madori)
room_names = ("n_rooms", "has_L", "has_D", "has_K", "has_S", "is_1R")
if parsed[0] == "FAILED":
	st.error(f"Unable to parse layout: {madori}")
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
		st.error("Area must be greater than 0.")
		st.stop()
	if stories_above < 1:
		st.error("Stories above must be at least 1.")
		st.stop()
	if floor_min > stories_above:
		st.error("Floor must not exceed stories above.")
		st.stop()
	try:
		r = valuate(attrs, asking_rent or None)
		finder = load_finder()
		comparables = finder.find(attrs)
		st.session_state.result = r
		st.session_state.comparables = comparables
	except Exception as exc:
		st.error(f"{type(exc).__name__}: {exc}")

result = st.session_state.result
comparables = st.session_state.comparables
if result is not None:
	st.metric("Estimated monthly rent", f"¥{result['estimate']:,.0f}")
	st.write(f"80% interval: ¥{result['lo']:,.0f} – ¥{result['hi']:,.0f}")
	if "label" in result:
		st.write(
			f"Position: {result['position']} | Gap: {result['gap_pct']:+.1%} | "
			f"Label: {result['label']}"
		)
	if result["confidence"] == "low":
		st.warning("Confidence is low; interpret this estimate carefully.")

	if comparables is not None:
		st.write(f"Comparable range: ¥{comparables['p25']:,.0f} – ¥{comparables['p75']:,.0f}")
		st.write(f"Comparable median: ¥{comparables['median']:,.0f}")
		st.write(f"Comparable listings: {comparables['n']}")
		if comparables["p25"] > result["hi"] or comparables["p75"] < result["lo"]:
			st.info("Similar listings suggest a different range from the model; treat this estimate with care.")
	else:
		st.info("No similar listings found.")
	st.caption("Results are estimates based on available listings and may not reflect current market conditions.")
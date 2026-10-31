from pathlib import Path
import json
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from src.map_data import map_frame
from app.i18n import t


@st.cache_data
def _load_geojson():
	with (ROOT / "app" / "data" / "tokyo_simplified.geojson").open(
		encoding="utf-8"
	) as file:
		return json.load(file)


@st.cache_data
def _load_stats():
	stats = pd.read_csv(ROOT / "data" / "interim" / "municipality_stats.csv")
	if "rent_per_m2" not in stats and "median_rent_per_m2" in stats:
		stats = stats.rename(columns={"median_rent_per_m2": "rent_per_m2"})
	return stats


def _selected_location(event):
	selection = getattr(event, "selection", None)
	if selection is None and isinstance(event, dict):
		selection = event.get("selection")
	points = getattr(selection, "points", None)
	if points is None and isinstance(selection, dict):
		points = selection.get("points")
	if not points:
		return None
	point = points[0]
	location = getattr(point, "location", None)
	return location if location is not None else point.get("location")


def render_map(lang):
	geojson = _load_geojson()
	stats = _load_stats()
	names = [
		feature["properties"]["ward_ja"]
		for feature in geojson.get("features", [])
		if feature.get("properties", {}).get("ward_ja")
	]

	metric = st.radio(
		t(lang, "map_metric"),
		["median_rent", "rent_per_m2"],
		format_func=lambda value: t(
			lang, "map_metric_rent" if value == "median_rent" else "map_metric_sqm"
		),
		horizontal=True,
	)
	df = map_frame(stats, names, metric).merge(
		stats[["municipality", "median_rent", "rent_per_m2"]],
		on="municipality",
		how="left",
		suffixes=("", "_stats"),
	)
	available = df[df["status"].eq("ok")]
	unavailable = df[~df["status"].eq("ok")]
	metric_label = t(
		lang, "map_metric_rent" if metric == "median_rent" else "map_metric_sqm"
	)

	fig = px.choropleth(
		available,
		geojson=geojson,
		locations="municipality",
		featureidkey="properties.ward_ja",
		color="value",
		color_continuous_scale="YlOrRd",
		hover_data=["n", "status"],
	)
	if not unavailable.empty:
		fig.add_trace(
			go.Choropleth(
				geojson=geojson,
				locations=unavailable["municipality"],
				z=[1] * len(unavailable),
				featureidkey="properties.ward_ja",
				colorscale=[[0, "#cccccc"], [1, "#cccccc"]],
				showscale=False,
				hoverinfo="skip",
			)
		)
	fig.update_coloraxes(
		colorbar_title=metric_label,
		colorbar_tickformat=",.0f",
	)
	fig.update_layout(
		paper_bgcolor="rgba(0,0,0,0)",
		plot_bgcolor="rgba(0,0,0,0)",
		height=450,
		margin=dict(l=0, r=0, t=0, b=0),
	)
	fig.update_geos(
		bgcolor="rgba(0,0,0,0)",
		fitbounds="locations",
		visible=False,
	)
	st.plotly_chart(fig, on_select="rerun", key="tokyo_map")

	selected = st.selectbox(
		t(lang, "map_select"),
		names,
		index=None,
		placeholder=t(lang, "map_select_prompt"),
	)
	if selected is not None:
		row = df[df["municipality"].eq(selected)]
		if not row.empty:
			record = row.iloc[0]
			if record["status"] == "ok":
				columns = st.columns(3)
				columns[0].metric(t(lang, "map_n"), f"{record['n']:,}")
				columns[1].metric(
					t(lang, "map_median_rent"), f"{record['median_rent']:,.0f}"
				)
				columns[2].metric(
					t(lang, "map_rent_per_m2"), f"{record['rent_per_m2']:,.0f}"
				)
			elif record["status"] == "low_sample":
				st.info(t(lang, "map_low_sample"))
			elif record["status"] == "no_data":
				st.info(t(lang, "map_no_data"))
	st.caption(t(lang, "map_credit"))

    
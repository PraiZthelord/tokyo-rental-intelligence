import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


def _yen(value):
	return int(np.rint(value))


def same_building_comps(val, idx, min_n=3) -> dict | None:
	"""Return price comparisons for other, differently labelled units."""
	required = {"building_key", "lookalike_id", "Price_yen", "area_m2"}
	if not required.issubset(val.columns):
		return None

	try:
		row = val.loc[idx]
		if not np.isscalar(row.get("building_key")):
			return None
		area = float(row["area_m2"])
		pool = val[
			(val["building_key"] == row["building_key"])
			& (val.index != idx)
			& (val["lookalike_id"] != row["lookalike_id"])
		]
	except (KeyError, TypeError, ValueError):
		return None

	if not np.isfinite(area) or area <= 0 or len(pool) < min_n:
		return None

	prices = pd.to_numeric(pool["Price_yen"], errors="coerce").to_numpy(float)
	areas = pd.to_numeric(pool["area_m2"], errors="coerce").to_numpy(float)
	valid = np.isfinite(prices) & np.isfinite(areas) & (areas > 0)
	ppm2 = prices[valid] / areas[valid]
	if len(ppm2) < min_n:
		return None

	return {
		"n": int(len(ppm2)),
		"median": _yen(np.median(ppm2) * area),
		"p25": _yen(np.percentile(ppm2, 25) * area),
		"p75": _yen(np.percentile(ppm2, 75) * area),
		"label": "Other units in the same building",
	}


class SimilarFinder:
	FEATURES = ["log_area", "age_years", "walk_min_nearest", "n_rooms", "stories_above"]
	WEIGHTS = np.array([3, 1, 1, 1.5, 0.5], dtype=float)
	K = 10

	def __init__(self, df):
		self._groups = {}
		if not isinstance(df, pd.DataFrame) or "municipality" not in df.columns:
			return

		for municipality, group in df.groupby("municipality", dropna=False):
			values = pd.DataFrame(index=group.index)
			for feature in self.FEATURES:
				if feature == "log_area" and feature not in group.columns and "area_m2" in group:
					values[feature] = np.log(pd.to_numeric(group["area_m2"], errors="coerce"))
				elif feature in group.columns:
					values[feature] = pd.to_numeric(group[feature], errors="coerce")
				else:
					values[feature] = np.nan

			if "Price_yen" not in group.columns or "area_m2" not in group.columns:
				continue
			rent = pd.to_numeric(group["Price_yen"], errors="coerce") / pd.to_numeric(
				group["area_m2"], errors="coerce"
			)
			usable = np.isfinite(rent.to_numpy(float)) & (rent.to_numpy(float) > 0)
			if not usable.any():
				continue

			values = values.iloc[usable]
			rents = rent.to_numpy(float)[usable]
			medians = values.median().to_numpy(float)
			medians = np.where(np.isfinite(medians), medians, 0.0)
			matrix = np.where(np.isfinite(values.to_numpy(float)), values.to_numpy(float), medians)
			scaler = StandardScaler().fit(matrix)
			scaled = scaler.transform(matrix) * self.WEIGHTS
			neighbors = NearestNeighbors(n_neighbors=min(self.K, len(matrix))).fit(scaled)
			self._groups[municipality] = (medians, scaler, neighbors, rents)

	def find(self, attrs: dict) -> dict | None:
		if not isinstance(attrs, dict) or "municipality" not in attrs:
			return None
		municipality = attrs["municipality"]
		try:
			medians, scaler, neighbors, rents = self._groups[municipality]
		except (KeyError, TypeError):
			return None

		try:
			area = float(attrs["area_m2"])
		except (KeyError, TypeError, ValueError):
			return None
		if not np.isfinite(area) or area <= 0:
			return None

		query = []
		for position, feature in enumerate(self.FEATURES):
			value = attrs.get(feature)
			if feature == "log_area" and value is None:
				value = np.log(area)
			try:
				value = float(value)
			except (TypeError, ValueError):
				value = np.nan
			query.append(value if np.isfinite(value) else medians[position])

		transformed = scaler.transform(np.asarray([query])) * self.WEIGHTS
		indices = neighbors.kneighbors(transformed, return_distance=False)[0]
		selected = rents[indices]
		return {
			"n": int(len(selected)),
			"median": _yen(np.median(selected) * area),
			"p25": _yen(np.percentile(selected, 25) * area),
			"p75": _yen(np.percentile(selected, 75) * area),
			"label": "Similar listings in the same municipality",
		}
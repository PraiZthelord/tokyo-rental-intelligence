# Function map_frame(stats, names, metric, min_n=100) -> DataFrame.
# stats has columns: municipality, n, median_rent, rent_per_m2.
# names is the list of municipality names from the GeoJSON.
# Return one row per name in names (same order) with columns:
#   municipality, n, value, status.
# value = stats[metric], status = "ok".
# If n < min_n: status = "low_sample" and value = NaN.
# If the name is missing from stats: status = "no_data", value = NaN, n = NaN.
# Raise ValueError if metric is not "median_rent" or "rent_per_m2".
# Use pandas only, no loops over rows if possible.

import pandas as pd


def map_frame(stats, names, metric, min_n=100):
	"""Return map-ready statistics in the order supplied by ``names``."""
	if metric not in {"median_rent", "rent_per_m2"}:
		raise ValueError(f"Unsupported metric: {metric}")

	values = stats[["municipality", "n", metric]].rename(columns={metric: "value"})
	result = pd.DataFrame({"municipality": names}).merge(
		values, on="municipality", how="left", sort=False, indicator=True
	)

	missing = result["_merge"].eq("left_only")
	low_sample = result["n"].lt(min_n) & ~missing
	result["status"] = "ok"
	result.loc[low_sample, "status"] = "low_sample"
	result.loc[missing, "status"] = "no_data"
	result.loc[low_sample | missing, "value"] = float("nan")

	return result[["municipality", "n", "value", "status"]]
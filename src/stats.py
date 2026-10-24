"""Municipality-level rental statistics."""

import numpy as np
import pandas as pd


def municipality_stats(df, min_n=100) -> pd.DataFrame:
	"""Return aggregate rental statistics grouped by municipality.

	The input frame is never modified.  Listings with invalid area or missing
	price are excluded only from the rent-per-square-metre statistic.
	"""
	required = ["municipality", "Price_yen", "area_m2"]
	missing = [column for column in required if column not in df.columns]
	if missing:
		raise KeyError(f"Missing required columns: {missing}")

	grouped = df.groupby("municipality", dropna=False)
	result = grouped.agg(
		n=("municipality", "size"),
		median_rent=("Price_yen", "median"),
		p25_rent=("Price_yen", lambda values: values.quantile(0.25)),
		p75_rent=("Price_yen", lambda values: values.quantile(0.75)),
		median_area=("area_m2", "median"),
	)

	valid = df.loc[df["area_m2"].gt(0) & df["Price_yen"].notna(),
				   ["municipality", "Price_yen", "area_m2"]].copy()
	valid["rent_per_m2"] = valid["Price_yen"] / valid["area_m2"]
	median_per_m2 = valid.groupby("municipality", dropna=False)["rent_per_m2"].median()
	result["median_rent_per_m2"] = median_per_m2

	if "age_years" in df.columns:
		result["median_age"] = grouped["age_years"].median()

	result["region"] = [
		"ward" if isinstance(name, str) and name.endswith("区")
		else "city" if isinstance(name, str) and name.endswith("市")
		else "town_village"
		for name in result.index
	]
	result["low_sample"] = result["n"] < min_n

	for column in ("median_rent", "p25_rent", "p75_rent"):
		result[column] = result[column].round(0)
	result["median_rent_per_m2"] = result["median_rent_per_m2"].round(1)

	result = result.reset_index()
	return result.sort_values("median_rent", ascending=False, na_position="last").reset_index(drop=True)

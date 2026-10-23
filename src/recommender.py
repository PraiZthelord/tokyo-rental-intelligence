import numpy as np
import pandas as pd


def madori_label(row):

	"""Reconstruct the room-plan label from the normalized room columns."""
	if bool(row.get("is_1R", False)):
		return "ワンルーム"

	rooms = row.get("n_rooms")
	if pd.isna(rooms):
		return ""
	try:
		number = str(int(float(rooms)))
	except (TypeError, ValueError):
		number = str(rooms).strip()

	suffix = "".join(
		part
		for column, part in (("has_S","S"), ("has_L","L"), ("has_D","D"), ("has_K","K"))
		if bool(row.get(column, False))
	)
	return number + suffix


def _scaled(values, reverse=False):
	values = pd.to_numeric(values, errors="coerce")
	low, high = values.min(), values.max()
	if pd.isna(low) or pd.isna(high) or high == low:
		return pd.Series(0.5, index=values.index)
	result = (values - low) / (high - low)
	return 1 - result if reverse else result


def recommend(val, prefs, weights=None, top_n=20):
	"""Filter and rank listings without changing the supplied valuation table."""
	required = [
		"has_L", "has_D", "has_K", "has_S", "is_1R", "n_rooms",
		"Price_yen", "estimate", "walk_min_nearest", "age_years", "area_m2",
		"municipality","lookalike_id","building_key","confidence"
	]
	missing = [c for c in required if c not in val.columns]
	if missing:
		raise KeyError(f"valuation table is missing columns: {missing}")

	prefs = prefs or {}
	defaults = {"value": 0.4, "walk": 0.25, "age": 0.2, "area": 0.15}
	if weights:
		defaults.update(weights)
	weights = defaults

	frame = val.copy()
	initial_count = len(frame)
	filter_removed = {}

	def apply_filter(name, mask):
		nonlocal frame
		mask = pd.Series(mask, index=frame.index).fillna(False).astype(bool)
		before = len(frame)
		frame = frame.loc[mask].copy()
		filter_removed[name] = before - len(frame)

	if prefs.get("max_rent") is not None:
		apply_filter("max_rent", pd.to_numeric(frame["Price_yen"], errors="coerce") <= prefs["max_rent"])
	if prefs.get("min_area") is not None:
		apply_filter("min_area", pd.to_numeric(frame["area_m2"], errors="coerce") >= prefs["min_area"])
	if prefs.get("madori") is not None:
		wanted = {str(value) for value in prefs["madori"]}
		apply_filter("madori", frame.apply(madori_label, axis=1).isin(wanted))
	if prefs.get("municipalities") is not None:
		apply_filter("municipalities", frame["municipality"].isin(prefs["municipalities"]))
	if prefs.get("max_walk") is not None:
		walk = pd.to_numeric(frame["walk_min_nearest"], errors="coerce")
		apply_filter("max_walk", walk.notna() & (walk <= prefs["max_walk"]))
	if prefs.get("max_age") is not None:
		apply_filter("max_age", pd.to_numeric(frame["age_years"], errors="coerce") <= prefs["max_age"])

	notes = []
	low_mask = frame["confidence"].eq("low") if "confidence" in frame else pd.Series(False, index=frame.index)
	low_count = int(low_mask.sum())
	if low_count:
		frame = frame.loc[~low_mask].copy()
		notes.append(f"Dropped {low_count} low-confidence row(s).")

	max_gap = prefs.get("max_gap", prefs.get("min_gap", -0.30))
	gap = (pd.to_numeric(frame["estimate"], errors="coerce") - pd.to_numeric(frame["Price_yen"], errors="coerce")) / pd.to_numeric(frame["estimate"], errors="coerce")
	extreme = gap > abs(max_gap)
	if extreme.sum():
		frame = frame.loc[~extreme].copy()
		notes.append(f"Excluded {int(extreme.sum())} listing(s) with a gap beyond {abs(max_gap):.0%} (likely model error).")

	duplicate_count = 0
	if "lookalike_id" in frame:
		key_cols = [c for c in ["Price_yen", "area_m2", "walk_min_nearest", "age_years", "municipality"] if c in frame]
		duplicate_mask = (frame["lookalike_id"].duplicated(keep="first") |
						  frame.duplicated(subset=key_cols, keep="first"))
		duplicate_count = int(duplicate_mask.sum())
		if duplicate_count:
			frame = frame.loc[~duplicate_mask].copy()
			notes.append(f"Dropped {duplicate_count} duplicate look-alike row(s).")

	output_columns = ["Price_yen", "estimate", "lo", "hi", "position", "gap_pct",
					  "walk_min_nearest", "age_years", "area_m2", "municipality",
					  "n_rooms", "score", "units_in_building"]
	if frame.empty:
		return pd.DataFrame(columns=output_columns), "No listings remain after applying the requested filters and safeguards."

	estimate = pd.to_numeric(frame["estimate"], errors="coerce")
	price = pd.to_numeric(frame["Price_yen"], errors="coerce")
	value = ((estimate - price) / estimate.replace(0, np.nan)).clip(-0.3, 0.3).fillna(0.0)
	walk_score = _scaled(frame["walk_min_nearest"], reverse=True)
	age_score = _scaled(frame["age_years"], reverse=True)
	area_score = _scaled(frame["area_m2"])
	frame["score"] = (weights["value"] * value + weights["walk"] * walk_score +
					  weights["age"] * age_score + weights["area"] * area_score)
	frame["units_in_building"] = frame.groupby("building_key")["building_key"].transform("size")
	frame = frame.sort_values("score", ascending=False).drop_duplicates("building_key", keep="first").head(top_n)

	if len(frame) < top_n and initial_count:
		name, removed = max(filter_removed.items(), key=lambda item: item[1], default=(None, 0))
		if name and removed:
			percentage = removed / initial_count * 100
			notes.append(f"{name} removed {percentage:.0f}% of candidates.")
	notes.append("Ranked by relatively low asking rent vs similar listings, walk, age and area.\nNot a guarantee of a good deal.")
	return frame.reindex(columns=output_columns), " ".join(notes)
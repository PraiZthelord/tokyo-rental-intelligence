# src/predict.py: load saved artifacts ONCE, then valuate listings. Never trains anything.
# Imports: json, joblib, numpy as np, pandas as pd, pathlib.Path.
#
# MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
#
# Module-level loading (cached in a dict, load lazily on first call):
#   q10, q50, q90 = joblib models from xgb_q10/q50/q90.joblib
#   cal = json from calibration.json (keys: q_band, q_global, edges, features, cat)
#
# def valuate(attrs: dict, asking_rent: float | None = None) -> dict:
#   1. Build a one-row DataFrame with columns cal["features"] + cal["cat"] from attrs.
#      Missing numeric keys become np.nan. Raise ValueError if "municipality" or "area_m2"
#      is missing or area_m2 <= 0.
#   2. Predict lo, mid, hi in LOG space with q10, q50, q90.
#      Fix crossing: lo = min(lo, mid), hi = max(hi, mid).
#   3. mid_yen = np.expm1(mid). Band from mid_yen using edges [0, 80000, 150000, inf]
#      -> "<80k", "80-150k", ">150k". q = cal["q_band"][band] (fallback cal["q_global"]).
#   4. lo_yen = np.expm1(lo - q); hi_yen = np.expm1(hi + q). All as plain Python floats,
#      rounded to the nearest yen.
#   5. confidence = "low" if municipality is in ["瑞穂町","日の出町","奥多摩町","檜原村"]
#      or area_m2 > 80, else "normal".
#   6. If asking_rent is given: position = "above" if asking_rent > hi_yen,
#      "below" if asking_rent < lo_yen, else "within"; gap_pct = (asking_rent - mid_yen)/mid_yen.
#      label: above -> "Relatively high compared with the model's expected range",
#             below -> "Relatively low compared with the model's expected range",
#             within -> "Within the expected range".
#      If confidence == "low", label = "Low confidence: " + label.
#      Never use the words "overpriced" or "underpriced".
#   7. Return dict: estimate, lo, hi, band, confidence, and (if asking_rent) position,
#      gap_pct, label.
# Do not retrain or refit anything. Do not mutate attrs.

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
_ARTIFACTS = {}


def _load_artifacts():
	if not _ARTIFACTS:
		_ARTIFACTS.update(
			q10=joblib.load(MODELS_DIR / "xgb_q10.joblib"),
			q50=joblib.load(MODELS_DIR / "xgb_q50.joblib"),
			q90=joblib.load(MODELS_DIR / "xgb_q90.joblib"),
			cal=json.loads((MODELS_DIR / "calibration.json").read_text(encoding="utf-8")),
		)
	return _ARTIFACTS


def valuate(attrs, asking_rent=None):
	artifacts = _load_artifacts()
	cal = artifacts["cal"]

	if "municipality" not in attrs or attrs["municipality"] is None:
		raise ValueError("municipality is required")
	if "area_m2" not in attrs or attrs["area_m2"] is None:
		raise ValueError("area_m2 is required")
	try:
		area_m2 = float(attrs["area_m2"])
	except (TypeError, ValueError) as exc:
		raise ValueError("area_m2 must be positive") from exc
	if not np.isfinite(area_m2) or area_m2 <= 0:
		raise ValueError("area_m2 must be positive")

	features = list(cal.get("features", []))
	categorical = list(cal.get("cat", []))
	columns = list(dict.fromkeys(features + categorical))
	row = {}
	for column in columns:
		if column in attrs:
			row[column] = attrs[column]
		elif column in categorical:
			row[column] = np.nan
		else:
			row[column] = np.nan
	row["area_m2"] = area_m2
	frame = pd.DataFrame([row], columns=columns)

	def predict(model):
		return float(np.asarray(model.predict(frame)).reshape(-1)[0])

	lo, mid, hi = predict(artifacts["q10"]), predict(artifacts["q50"]), predict(artifacts["q90"])
	lo = min(lo, mid)
	hi = max(hi, mid)
	mid_yen = float(np.expm1(mid))

	if mid_yen < 80000:
		band = "<80k"
	elif mid_yen <= 150000:
		band = "80-150k"
	else:
		band = ">150k"
	q = cal.get("q_band", {}).get(band, cal.get("q_global", 0))
	lo_yen = float(round(np.expm1(lo - float(q))))
	hi_yen = float(round(np.expm1(hi + float(q))))
	estimate = float(round(mid_yen))

	municipality = attrs["municipality"]
	confidence = (
		"low"
		if municipality in ["瑞穂町", "日の出町", "奥多摩町", "檜原村"] or area_m2 > 80
		else "normal"
	)
	result = {
		"estimate": estimate,
		"lo": lo_yen,
		"hi": hi_yen,
		"band": band,
		"confidence": confidence,
	}
	if asking_rent is not None:
		asking_rent = float(asking_rent)
		if asking_rent > hi_yen:
			position = "above"
			label = "Relatively high compared with the model's expected range"
		elif asking_rent < lo_yen:
			position = "below"
			label = "Relatively low compared with the model's expected range"
		else:
			position = "within"
			label = "Within the expected range"
		if confidence == "low":
			label = "Low confidence: " + label
		result.update(
			position=position,
			gap_pct=float((asking_rent - mid_yen) / mid_yen),
			label=label,
		)
	return result

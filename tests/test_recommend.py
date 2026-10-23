import numpy as np
import pandas as pd
from src.recommender import recommend, madori_label

def make_val():
    return pd.DataFrame({
        "Price_yen":        [60000, 80000, 90000, 120000, 70000, 70000],
        "estimate":         [80000, 85000, 90000, 100000, 75000, 75000],
        "lo":               [65000, 70000, 75000,  85000, 62000, 62000],
        "hi":               [95000, 100000, 105000, 118000, 90000, 90000],
        "position":         ["below","within","within","above","within","within"],
        "gap_pct":          [-0.25, -0.059, 0.0, 0.2, -0.067, -0.067],
        "walk_min_nearest": [5, 8, 12, 3, 6, 6],
        "age_years":        [10, 5, 20, 2, 8, 8],
        "area_m2":          [30, 35, 40, 45, 32, 32],
        "municipality":     ["世田谷区"]*6,
        "n_rooms":          [1, 1, 2, 2, 1, 1],
        "has_L":            [0, 1, 1, 1, 1, 1],
        "has_D":            [0, 1, 1, 1, 1, 1],
        "has_K":            [1, 1, 1, 1, 1, 1],
        "has_S":            [0, 0, 0, 0, 0, 0],
        "is_1R":            [0, 0, 0, 0, 0, 0],
        "lookalike_id":     [1, 2, 3, 4, 5, 5],      # rows 4 and 5 are twins
        "confidence":       ["normal","normal","normal","normal","normal","normal"],
        "building_key":     ["b1", "b2", "b3", "b4", "b5", "b6"]
    })

def test_filters_respected():
    out, _ = recommend(make_val(), {"max_rent": 85000, "max_walk": 10})
    assert (out["Price_yen"] <= 85000).all()
    assert (out["walk_min_nearest"] <= 10).all()

def test_no_lookalike_duplicates():
    out, _ = recommend(make_val(), {})
    assert len(out) == 5          # rows 4 and 5 are twins, only one survives

def test_low_confidence_dropped():
    v = make_val(); v.loc[0, "confidence"] = "low"
    out, msg = recommend(v, {})
    assert 60000 not in out["Price_yen"].values

def test_value_only_weights_sorted_by_gap():
    out, _ = recommend(make_val(), {}, weights={"value":1,"walk":0,"age":0,"area":0})
    assert out["gap_pct"].is_monotonic_increasing   # most negative first

def test_impossible_filter_returns_empty_with_message():
    out, msg = recommend(make_val(), {"max_rent": 10000})
    assert len(out) == 0 and len(msg) > 0

def test_no_identifying_columns():
    out, _ = recommend(make_val(), {})
    assert not {"jnc","building_key","Listing Title","Links to Listing"} & set(out.columns)

def test_input_not_modified():
    v = make_val(); before = v.copy()
    recommend(v, {"max_rent": 85000})
    pd.testing.assert_frame_equal(v, before)

def test_madori_label():
    r = make_val().iloc[1]                    # n_rooms=1, L, D, K
    assert madori_label(r) == "1LDK"


# Add a test unit for n_rooms=3, has_S=1, has_L=1, has_D=1, has_K=1 -> "3SLDK".

def test_madori_label_3sl():
    r = make_val().iloc[3]                    # n_rooms=2, L, D, K
    r["n_rooms"] = 3
    r["has_S"] = 1
    assert madori_label(r) == "3SLDK"


def test_one_row_per_building():
    v = make_val(); v["building_key"] = ["a","a","b","c","d","e"]
    out, _ = recommend(v, {})
    assert out.shape[0] == 4   # building "a" appears once

def test_extreme_gap_excluded():
    v = make_val(); v.loc[0, "Price_yen"] = 20000   # gap far below -0.30
    out, _ = recommend(v, {})
    assert 20000 not in out["Price_yen"].values

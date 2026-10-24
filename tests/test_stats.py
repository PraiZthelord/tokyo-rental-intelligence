import pandas as pd
from src.stats import municipality_stats

def make_df():
    return pd.DataFrame({
        "municipality": ["A区"]*3 + ["B市"]*2 + ["C町"],
        "Price_yen":    [100000, 120000, 140000, 60000, 80000, 50000],
        "area_m2":      [20, 30, 40, 20, 40, 25],
    })

def test_counts_and_medians():
    s = municipality_stats(make_df(), min_n=2).set_index("municipality")
    assert s.loc["A区", "n"] == 3
    assert s.loc["A区", "median_rent"] == 120000
    assert s.loc["B市", "median_rent"] == 70000

def test_region_and_low_sample():
    s = municipality_stats(make_df(), min_n=2).set_index("municipality")
    assert s.loc["A区", "region"] == "ward"
    assert s.loc["B市", "region"] == "city"
    assert s.loc["C町", "region"] == "town_village"
    assert bool(s.loc["C町", "low_sample"]) and not bool(s.loc["A区", "low_sample"])

def test_sorted_descending():
    s = municipality_stats(make_df(), min_n=2)
    assert s["median_rent"].is_monotonic_decreasing

def test_missing_column_raises():
    import pytest
    with pytest.raises(KeyError):
        municipality_stats(make_df().drop(columns="area_m2"))

def test_no_identifying_columns():
    s = municipality_stats(make_df())
    assert not {"jnc", "building_key", "Listing Title", "Links to Listing"} & set(s.columns)
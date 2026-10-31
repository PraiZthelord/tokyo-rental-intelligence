import pandas as pd
from src.map_data import map_frame

def test_map_frame_statuses():
    stats = pd.DataFrame({
        "municipality": ["新宿区", "町田市"],
        "n": [5000, 40],
        "median_rent": [120000, 80000],
        "rent_per_m2": [4000.0, 2500.0],
    })
    names = ["新宿区", "町田市", "檜原村"]
    out = map_frame(stats, names, metric="median_rent", min_n=100).set_index("municipality")
    assert list(out.index) == names                      # one row per map name, same order
    assert out.loc["新宿区", "status"] == "ok"
    assert out.loc["新宿区", "value"] == 120000
    assert out.loc["町田市", "status"] == "low_sample"   # n < min_n
    assert pd.isna(out.loc["町田市", "value"])           # not colored
    assert out.loc["檜原村", "status"] == "no_data"      # missing from stats
    assert pd.isna(out.loc["檜原村", "value"])
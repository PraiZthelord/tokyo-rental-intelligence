from src.predict import valuate

SETAGAYA = dict(area_m2=25, age_years=10, floor_min=1, stories_above=2, walk_min_nearest=5,
                n_rooms=1, has_L=0, has_D=0, has_K=1, has_S=0, is_1R=0, municipality="世田谷区")

def test_interval_contains_estimate():
    r = valuate(SETAGAYA)
    assert r["lo"] < r["estimate"] < r["hi"]

def test_matches_notebook():
    r = valuate(SETAGAYA)
    assert abs(r["estimate"] - 82131) <= 1 and abs(r["lo"] - 69683) <= 1 and abs(r["hi"] - 96478) <= 1

def test_asking_above():
    assert valuate(SETAGAYA, asking_rent=200000)["position"] == "above"

def test_asking_within():
    assert valuate(SETAGAYA, asking_rent=82000)["position"] == "within"

def test_gap_zero_when_asking_equals_estimate():
    r = valuate(SETAGAYA)
    r2 = valuate(SETAGAYA, asking_rent=r["estimate"])
    assert abs(r2["gap_pct"]) < 0.001 and r2["position"] == "within"

def test_gap_formula():
    r = valuate(SETAGAYA)
    ask = r["estimate"] * 1.5
    r2 = valuate(SETAGAYA, asking_rent=ask)
    assert abs(r2["gap_pct"] - 0.5) < 0.001

def test_position_boundaries():
    r = valuate(SETAGAYA)
    assert valuate(SETAGAYA, asking_rent=r["hi"] + 1000)["position"] == "above"
    assert valuate(SETAGAYA, asking_rent=r["lo"] - 1000)["position"] == "below"
    assert valuate(SETAGAYA, asking_rent=(r["lo"] + r["hi"]) / 2)["position"] == "within"

def test_gap_negative_when_below_estimate():
    r = valuate(SETAGAYA)
    assert valuate(SETAGAYA, asking_rent=r["estimate"] * 0.5)["gap_pct"] < 0

def test_no_gap_keys_without_asking_rent():
    r = valuate(SETAGAYA)
    assert "gap_pct" not in r and "position" not in r and "label" not in r

def test_label_wording():
    r = valuate(SETAGAYA, asking_rent=1_000_000)
    assert "overpriced" not in r["label"].lower()

def test_low_confidence_town():
    r = valuate({**SETAGAYA, "municipality": "瑞穂町"}, asking_rent=50000)
    assert r["confidence"] == "low" and r["label"].startswith("Low confidence")

def test_bad_input():
    import pytest
    with pytest.raises(ValueError):
        valuate({**SETAGAYA, "area_m2": 0})


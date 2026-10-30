import json
from pathlib import Path

PATH = Path("app/data/tokyo_simplified.geojson")

def test_geojson_clean():
    gj = json.loads(PATH.read_text(encoding="utf-8"))
    names = [f["properties"]["ward_ja"] for f in gj["features"]]
    assert len(names) == len(set(names))            # no duplicates
    assert "所属未定地" not in names                 # placeholder dropped
    assert "小笠原村" not in names                   # islands dropped
    assert "新宿区" in names and "八王子市" in names
    assert len(names) == 53                         # 62 - 9 islands
    assert PATH.stat().st_size < 1_500_000          # simplified
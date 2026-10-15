from src.geo import parse_location,MUNICIPALITIES

def test_akiruno():
    assert parse_location("東京都あきる野市伊奈") == ("あきる野市", "伊奈")

def test_machida():
    assert parse_location("東京都町田市原町田") == ("町田市", "原町田")

def test_town_with_number():
    assert parse_location("東京都青梅市上町 2") == ("青梅市", "上町 2")

def test_higashimurayama():
    assert parse_location("東京都東村山市本町") == ("東村山市", "本町")

def test_musashimurayama():
    assert parse_location("東京都武蔵村山市学園") == ("武蔵村山市", "学園")

def test_hamura():
    assert parse_location("東京都羽村市緑ケ丘") == ("羽村市", "緑ケ丘")

def test_gun_prefix_mizuho():
    assert parse_location("東京都西多摩郡瑞穂町箱根ケ崎") == ("瑞穂町", "箱根ケ崎")

def test_gun_prefix_okutama():
    assert parse_location("東京都西多摩郡奥多摩町氷川") == ("奥多摩町", "氷川")

def test_ward():
    assert parse_location("東京都千代田区丸の内") == ("千代田区", "丸の内")

def test_unknown():
    assert parse_location("abc") == ("FAILED", None)

def test_list_has_62():
    from src.geo import MUNICIPALITIES
    assert len(MUNICIPALITIES) == 62



'''Write pytest tests for make_building_key in src/geo.py (file: tests/test_keys.py).
The function takes a pandas Series with these fields only:
"Listing Title", "municipality", "town", "stories_above", "stories_below",
"Distances to Railway Stations"
and returns a string key. It never raises.

Use a helper to build rows:
def row(title, muni, town, above, below, stations="S1"): return pd.Series({...})

One test function per case, using assert:

Same key expected:
- Same named building, identical fields -> keys equal
- Title "ルアナ" vs " ル ア ナ " (extra spaces) -> keys equal
- Title "ルアナ" vs full-width "ルアナ" spelled with full-width characters -> keys equal
- Auto title "京王相模原線 稲城駅 2階建 築10年" with same station string, different
  nothing else -> keys equal

Different key expected:
- "ルアナ" vs "アウローラ南多摩", same municipality/town/stories -> keys differ
- Same named title, different town -> keys differ
- Same named title, different stories_above -> keys differ
- Auto title "京王相模原線 稲城駅 2階建 築10年" with station string "S1" vs "S2" -> keys differ
- NAMED title with station string "S1" vs "S2" -> keys EQUAL (station string is only
  used for auto-generated titles)

Robustness:
- Missing values (None / NaN) in town or stories -> returns a str, does not raise
- Return type is always str

Import with: from src.geo import make_building_key
Do not modify make_building_key. Do not add tests that are not listed.'''

from src.geo import make_building_key
import pandas as pd
def row(title, muni, town, above, below, stations="S1"):
    return pd.Series({
        "Listing Title": title,
        "municipality": muni,
        "town": town,
        "stories_above": above,
        "stories_below": below,
        "Distances to Railway Stations": stations
    })
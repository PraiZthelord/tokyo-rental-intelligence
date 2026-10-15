import pandas as pd
from src.geo import make_building_key

def row(title, muni, town, above, below, stations="S1"):
    return pd.Series({"Listing Title": title, "municipality": muni, "town": town,
                      "stories_above": above, "stories_below": below,
                      "Distances to Railway Stations": stations})

def test_same_building_different_unit_same_key():
    assert make_building_key(row("ルアナ", "あきる野市", "伊奈", 2, 0)) == \
           make_building_key(row("ルアナ", "あきる野市", "伊奈", 2, 0))

def test_different_named_buildings_differ():
    assert make_building_key(row("ルアナ", "あきる野市", "伊奈", 2, 0)) != \
           make_building_key(row("アウローラ南多摩", "あきる野市", "伊奈", 2, 0))

def test_fullwidth_and_spaces_same_key():
    assert make_building_key(row("ルアナ", "あきる野市", "伊奈", 2, 0)) == \
           make_building_key(row(" ル ア ナ ", "あきる野市", "伊奈", 2, 0))

def test_auto_title_station_string_matters():
    t = "京王相模原線 稲城駅 2階建 築10年"
    assert make_building_key(row(t, "稲城市", "矢野口", 2, 0, "S1")) != \
           make_building_key(row(t, "稲城市", "矢野口", 2, 0, "S2"))
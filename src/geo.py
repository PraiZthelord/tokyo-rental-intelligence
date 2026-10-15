# src/geo.py
import unicodedata


MUNICIPALITIES = [
    # 23 wards
    "千代田区", "中央区", "港区", "新宿区", "文京区", "台東区", "墨田区", "江東区",
    "品川区", "目黒区", "大田区", "世田谷区", "渋谷区", "中野区", "杉並区", "豊島区",
    "北区", "荒川区", "板橋区", "練馬区", "足立区", "葛飾区", "江戸川区",
    # 26 cities
    "八王子市", "立川市", "武蔵野市", "三鷹市", "青梅市", "府中市", "昭島市", "調布市",
    "町田市", "小金井市", "小平市", "日野市", "東村山市", "国分寺市", "国立市", "福生市",
    "狛江市", "東大和市", "清瀬市", "東久留米市", "武蔵村山市", "多摩市", "稲城市",
    "羽村市", "あきる野市", "西東京市",
    # towns and villages
    "瑞穂町", "日の出町", "檜原村", "奥多摩町",
    "大島町", "利島村", "新島村", "神津島村", "三宅村", "御蔵島村", "八丈町", "青ヶ島村", "小笠原村",
]


_SORTED = sorted(MUNICIPALITIES, key=len, reverse=True)  # longest first

def parse_location(location):
    s = unicodedata.normalize("NFKC", str(location)).strip()
    if not s.startswith("東京都"):
        return ("FAILED", None)
    rest = s[len("東京都"):]
    if "郡" in rest[:6]:                      # skip a prefix like 西多摩郡
        rest = rest.split("郡", 1)[1]
    for name in _SORTED:
        if rest.startswith(name):
            return (name, rest[len(name):])
    return ("FAILED", None)


# make_building_key(row) -> str
# Purpose: a group label so all units of one building share the same key (for grouped CV).
# row is a pandas Series with these columns ONLY:
#   "Listing Title", "municipality", "town", "stories_above", "stories_below",
#   "Distances to Railway Stations"
#
# Key = parts joined with "|":
#   1. title: unicodedata NFKC, then remove ALL whitespace (spaces, full-width spaces)
#   2. municipality
#   3. town
#   4. stories_above
#   5. stories_below
#
# If the title is auto-generated (re.fullmatch(r".+線 .+駅 \d+階建 (築\d+年|新築)" on the
# NFKC-normalized title, checked BEFORE removing whitespace), also append the raw
# "Distances to Railway Stations" string (NFKC, whitespace removed) as a 6th part.
#
# Do NOT use floor, rent, area, rooms, age, or listing ID in the key.
# Convert every part with str(). Missing values become the empty string "".
# Never raise. Return a string. Do not modify the row.
import re
import unicodedata

def make_building_key(row):
    title = unicodedata.normalize("NFKC", str(row.get("Listing Title", ""))).replace(" ", "")
    muni = str(row.get("municipality", ""))
    town = str(row.get("town", ""))
    stories_above = str(row.get("stories_above", ""))
    stories_below = str(row.get("stories_below", ""))
    key_parts = [title, muni, town, stories_above, stories_below]

    # Check if the title is auto-generated
    normalized_title = unicodedata.normalize("NFKC", str(row.get("Listing Title", "")))
    if re.fullmatch(r".+線 .+駅 \d+階建 (築\d+年|新築)", normalized_title):
        distances = unicodedata.normalize("NFKC", str(row.get("Distances to Railway Stations", ""))).replace(" ", "")
        key_parts.append(distances)

    return "|".join(key_parts)
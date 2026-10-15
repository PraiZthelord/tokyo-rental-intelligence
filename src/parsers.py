import unicodedata
# parse_stories(text) -> (stories_above,stories_below)
# Input Examples: "2階建"-> (2,0), "3階建/地下1階" -> (3,1), "地下1階/地上2階建" -> (2,1)

# Anything unrecognized should be returned as None. For example, "2階建/地下1階" should return (2,1), but "2階建/地下1階/屋上" should return None.

import re

def parse_stories(text):
    s = unicodedata.normalize("NFKC", str(text)).strip()
    if s == "平屋":
        return (1, 0)
    m = re.fullmatch(r"(?:地下(\d+))?(?:地上)?(\d+)階建", s)
    if m:
        below = int(m.group(1)) if m.group(1) else 0
        above = int(m.group(2))
        return (above, below)
    return ("FAILED", None)


# parse_floor(text) -> (floor_min, floor_max, is_multi_floor)
# Input is a SUUMO floor string. Normalize with unicodedata NFKC first, then strip.
# Examples:
#   "1階"    -> (1, 1, 0)
#   "12階"   -> (12, 12, 0)
#   "1-2階"  -> (1, 2, 1)       floor range, is_multi_floor = 1
#   "B1階"   -> (-1, -1, 0)     B means basement, encode as a negative number
#   "B1-1階" -> (-1, 1, 1)      range starting in the basement
#   "1-階"   -> (1, 1, 1)       open-ended range: floor_max = floor_min, is_multi_floor = 1
#   "-"      -> (None, None, None)   missing floor, not a parse failure
# Anything else (e.g. "M1階", "1B1階", "abc") -> ("FAILED", None, None)
# Use re.fullmatch so partial matches are rejected. Never raise an exception.
# Do not guess or fix unknown formats.
def parse_floor(text):
    s = unicodedata.normalize("NFKC", str(text)).strip()
    if s == "-":
        return (None, None, None)
    m = re.fullmatch(r"(B?)(\d+)(?:(-)(?:(B?)(\d+))?)?階", s)
    if m:
        floor_min = int(m.group(2)) * (-1 if m.group(1) else 1)
        if m.group(5):
            floor_max = int(m.group(5)) * (-1 if m.group(4) else 1)
        else:
            floor_max = floor_min
        is_multi_floor = 1 if m.group(3) else 0
        return (floor_min, floor_max, is_multi_floor)
    return ("FAILED", None, None)



# parse_area(area m) -> (area)as float
# Examples 19.87m ->19.87, 20m -> 20.0
# Anything else -> ("FAILED", None)
def parse_area(text):
    s = unicodedata.normalize("NFKC", str(text)).strip()
    m = re.fullmatch(r"(\d+(?:\.\d+)?)m", s)
    if m:
        return float(m.group(1))
    return ("FAILED", None)



#for building age parser
#parse_buildig_age(text) -> (age) as int
#Examples "築10年" -> 10, "築1年" -> 1

# Anything else -> ("FAILED", None)
def parse_building_age(text):
    s = unicodedata.normalize("NFKC", str(text)).strip()
    if s == "新築":
        return (0, 1)
    m = re.fullmatch(r"築(\d+)年(以上)?", s)
    if m:
        return (int(m.group(1)), 0)
    return ("FAILED", None)

# Room parser
# parse_rooms(text) -> rooms as int
# Examples "1K" -> 1, "2LDK" -> 2, "3LDK" -> 3 1SLDK-> 1,3K -> 3, ワンルーム -> 1R -> 1, 1DK->1 ,1S->1, 1SK->1 
# Create Different Boolean columns like is_sk,is_ldk,is_r according to the room type.
# Anything else -> ("FAILED", None)


def parse_rooms(text):
    s = unicodedata.normalize("NFKC", str(text)).strip()
    if s in ("ワンルーム", "1R"):
        return (1, 0, 0, 0, 0, 1)
    m = re.fullmatch(r"(\d+)(S?)(L?)(D?)(K)", s)
    if m:
        n = int(m.group(1))
        return (n, int(bool(m.group(3))), int(bool(m.group(4))),
                1, int(bool(m.group(2))), 0)
    return ("FAILED", None, None, None, None, None)


# parse_station_entry(entry) -> dict or None
# Input is ONE entry (already split on commas). Normalize with NFKC first.
# Three formats:
#   walk: "西武新宿線/東伏見駅 歩3分" -> mode="walk", walk_min=3
#   bus:  "JR中央線/三鷹駅 バス23分 (バス停)東伏見駅 歩3分" -> mode="bus", bus_min=23, bus_stop_walk_min=3, walk_min=None
#   car:  "JR常磐線/亀有駅 車14分(4.1km)" -> mode="car", car_min=14, car_km=4.1, walk_min=None
# Return dict with keys: line, station, mode, walk_min, bus_min, bus_stop_walk_min, car_min, car_km
# IMPORTANT: for bus entries the trailing 歩N分 is the walk to the bus stop, NOT to the station.
# Check bus and car patterns BEFORE the walk pattern. Use re.fullmatch.
# Unrecognised entry -> return None. Never raise.
def parse_station_entry(entry):
    s = unicodedata.normalize("NFKC", str(entry)).strip()
    m = re.fullmatch(r"([^/]+)/([^/ ]+) バス(\d+)分 \(バス停\)(.+) 歩(\d+)分", s)
    if m:
        return {
            "line": m.group(1),
            "station": m.group(2),
            "mode": "bus",
            "walk_min": None,
            "bus_min": int(m.group(3)),
            "bus_stop_walk_min": int(m.group(5)),
            "car_min": None,
            "car_km": None
        }
    m = re.fullmatch(r"([^/]+)/([^/]+) 車(\d+)分\(([\d.]+)km\)", s)
    if m:
        return {
            "line": m.group(1),
            "station": m.group(2),
            "mode": "car",
            "walk_min": None,
            "bus_min": None,
            "bus_stop_walk_min": None,
            "car_min": int(m.group(3)),
            "car_km": float(m.group(4))
        }
    m = re.fullmatch(r"([^/]+)/([^/]+) 歩(\d+)分", s)
    if m:
        return {
            "line": m.group(1),
            "station": m.group(2),
            "mode": "walk",
            "walk_min": int(m.group(3)),
            "bus_min": None,
            "bus_stop_walk_min": None,
            "car_min": None,
            "car_km": None
        }
    return None



# Define a parser to parse listing title and check if the listing title = info of(Distances to railway station, stories tall, building age)columns using regex 
# Example : parsing through this format "京王相模原線 京王よみうりランド駅 2階建 築14年	"
def parse_listing_title(title):
    s = unicodedata.normalize("NFKC", str(title)).strip()
    m = re.fullmatch(r"([^/]+)/([^/]+) (\d+)階建 築(\d+)年", s)
    if m:
        return {
            "line": m.group(1),
            "station": m.group(2),
            "stories": int(m.group(3)),
            "building_age": int(m.group(4))
        }
    return None



# Define a parser to parse location with MUNICIPALITY imported from src/geo.py 
# Run it on the column, then compare: df["municipality"].value_counts() should show 東村山市, 武蔁村山市 and 羽村市 spelled in full, the four 西多摩郡 towns split out, and 0 failures.


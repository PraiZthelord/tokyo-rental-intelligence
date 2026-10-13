import unicodedata
# parse_stories(text) -> (stories_above,stories_below)
# Input Examples: "2階建"-> (2,0), "3階建/地下1階" -> (3,1), "地下1階/地上2階建" -> (2,1)

# Anything unrecognized should be returned as None. For example, "2階建/地下1階" should return (2,1), but "2階建/地下1階/屋上" should return None.

import re

def parse_stories(text):
    s = unicodedata.normalize("NFKC", str(text)).strip()
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
# For 新築 -> 新築 for now 
# Anything else -> ("FAILED", None)
def parse_building_age(text):
    s = unicodedata.normalize("NFKC", str(text)).strip()
    if s == "新築":
        return "新築"
    m = re.fullmatch(r"築(\d+)年", s)
    if m:
        return int(m.group(1))
    return ("FAILED", None)
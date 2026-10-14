
from src.parsers import parse_stories

def test_stories_hiraya():
    assert parse_stories("平屋") == (1, 0)

def test_stories_simple():
    assert parse_stories("2階建") == (2, 0)

def test_stories_two_digits():
    assert parse_stories("10階建") == (10, 0)

def test_stories_basement():
    assert parse_stories("地下1地上38階建") == (38, 1)

def test_stories_unknown():
    assert parse_stories("abc") == ("FAILED", None)




#   "1階"    -> (1, 1, 0)
#   "12階"   -> (12, 12, 0)
#   "1-2階"  -> (1, 2, 1)       floor range, is_multi_floor = 1
#   "B1階"   -> (-1, -1, 0)     B means basement, encode as a negative number
#   "B1-1階" -> (-1, 1, 1)      range starting in the basement
#   "1-階"   -> (1, 1, 1)       open-ended range: floor_max = floor_min, is_multi_floor = 1
#   "-"      -> (None, None, None)   missing floor, not a parse failure
# Anything else (e.g. "M1階", "1B1階", "abc") -> ("FAILED", None, None)



def test_floor_simple():
    from src.parsers import parse_floor
    assert parse_floor("1階") == (1, 1, 0)
    assert parse_floor("12階") == (12, 12, 0)
    assert parse_floor("1-2階") == (1, 2, 1)
    assert parse_floor("B1階") == (-1, -1, 0)
    assert parse_floor("B1-1階") == (-1, 1, 1)
    assert parse_floor("1-階") == (1, 1, 1)
    assert parse_floor("-") == (None, None, None)
    assert parse_floor("M1階") == ("FAILED", None, None)
    assert parse_floor("abc") == ("FAILED", None, None)
    


# test parse_area 
# Examples 19.87m ->19.87, 20m -> 20.0
def test_parse_area():
    from src.parsers import parse_area
    assert parse_area("19.87m") == 19.87
    assert parse_area("20m") == 20.0
    assert parse_area("abc") == ("FAILED", None)

from src.parsers import parse_building_age
# test Building Age parser
# Examples "築10年" -> 10, "築1年" -> 1, 新築 -> 新築

def test_age_new():
    assert parse_building_age("新築") == (0, 1)

def test_age_normal():
    assert parse_building_age("築14年") == (14, 0)

def test_age_one_digit():
    assert parse_building_age("築1年") == (1, 0)

def test_age_two_digit():
    assert parse_building_age("築77年") == (77, 0)

def test_age_fullwidth_digits():
    assert parse_building_age("築１４年") == (14, 0)

def test_age_extra_spaces():
    assert parse_building_age(" 築14年 ") == (14, 0)

def test_age_unknown():
    assert parse_building_age("abc") == ("FAILED", None)

def test_age_partial_match_rejected():
    assert parse_building_age("築14年abc") == ("FAILED", None)

def test_age_or_more():
    assert parse_building_age("築99年以上") == (99, 0)

''' Write pytest tests for parse_rooms in src/parsers.py (file: tests/test_parsers.py).
The function returns a 6-tuple: (n_rooms, has_L, has_D, has_K, has_S, is_1R).
Failure returns ("FAILED", None, None, None, None, None). It never raises.

#One test function per case, using assert ==:
- "1K"    -> (1, 0, 0, 1, 0, 0)
- "2DK"   -> (2, 0, 1, 1, 0, 0)
- "2LDK"  -> (2, 1, 1, 1, 0, 0)
- "1SK"   -> (1, 0, 0, 1, 1, 0)
- "3SLDK" -> (3, 1, 1, 1, 1, 0)
- "1LK"   -> (1, 1, 0, 1, 0, 0)
- "2SLK"  -> (2, 1, 0, 1, 1, 0)
- "ワンルーム" -> (1, 0, 0, 0, 0, 1)
- "10SLDK" -> (10, 1, 1, 1, 1, 0)   (two-digit room count)
- "２ＬＤＫ" (full-width) -> (2, 1, 1, 1, 0, 0)
- " 2LDK " (spaces) -> (2, 1, 1, 1, 0, 0)

Failure cases, each expecting the FAILED tuple:
- "abc", "", "2LDKX" (trailing junk), "LDK" (no number), "2KL" (wrong letter order), "3R"

Import with: from src.parsers import parse_rooms
Do not modify parse_rooms. Do not add any test that is not listed.'''

def test_parse_rooms_1K():
    from src.parsers import parse_rooms
    assert parse_rooms("1K") == (1, 0, 0, 1, 0, 0)
    assert parse_rooms("2DK") == (2, 0, 1, 1, 0, 0)
    assert parse_rooms("2LDK") == (2, 1, 1, 1, 0, 0)
    assert parse_rooms("1SLDK") == (1, 1, 1, 1, 1, 0)
    assert parse_rooms("1SK") == (1, 0, 0, 1, 1, 0)
    assert parse_rooms("3SLDK") == (3, 1, 1, 1, 1, 0)
    assert parse_rooms("1LK") == (1, 1, 0, 1, 0, 0)
    assert parse_rooms("2SLK") == (2, 1, 0, 1, 1, 0)
    assert parse_rooms("ワンルーム") == (1, 0, 0, 0, 0, 1)
    assert parse_rooms("10SLDK") == (10, 1, 1, 1, 1, 0)
    assert parse_rooms("２ＬＤＫ") == (2, 1, 1, 1, 0, 0)
    assert parse_rooms(" 2LDK ") == (2, 1, 1, 1, 0, 0)


    
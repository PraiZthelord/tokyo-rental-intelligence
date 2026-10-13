
from src.parsers import parse_stories
from src.parsers import parse_floor



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
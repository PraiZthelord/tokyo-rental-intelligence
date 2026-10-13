
from src.parsers import parse_stories




def test_stories_simple():
    assert parse_stories("2階建") == (2, 0)

def test_stories_two_digits():
    assert parse_stories("10階建") == (10, 0)

def test_stories_basement():
    assert parse_stories("地下1地上38階建") == (38, 1)

def test_stories_unknown():
    assert parse_stories("abc") == ("FAILED", None)
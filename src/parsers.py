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
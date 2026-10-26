import pytest

from app.i18n import TEXT, t


def test_same_keys():
	assert TEXT["en"].keys() == TEXT["ja"].keys()


def test_no_empty_values():
	for language in ("en", "ja"):
		assert all(isinstance(value, str) and value for value in TEXT[language].values())


def test_missing_key_raises():
	with pytest.raises(KeyError):
		t("en", "nope")


def test_no_forbidden_words():
	assert all(
		word not in value.lower()
		for value in TEXT["en"].values()
		for word in ("overpriced", "underpriced")
	)


import re
from pathlib import Path
from app.i18n import TEXT

def test_all_used_keys_exist():
    src = Path("app/main.py").read_text(encoding="utf-8")
    used = set(re.findall(r't\(lang,\s*"(\w+)"\)', src))
    assert used <= set(TEXT["en"]), sorted(used - set(TEXT["en"]))
    assert used <= set(TEXT["ja"]), sorted(used - set(TEXT["ja"]))

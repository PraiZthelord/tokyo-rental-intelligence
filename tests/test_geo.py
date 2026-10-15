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
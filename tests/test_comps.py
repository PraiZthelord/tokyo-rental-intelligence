import pandas as pd

from src.comps import SimilarFinder, same_building_comps


def make_val():
	return pd.DataFrame(
		[
			["b1", 1, 60000, 30, "A区", 5, 6, 1, 2],
			["b1", 2, 90000, 30, "A区", 6, 7, 2, 2],
			["b1", 3, 120000, 30, "A区", 7, 8, 2, 3],
			["b1", 4, 90000, 30, "A区", 8, 9, 3, 3],
			["b2", 5, 70000, 25, "A区", 5, 5, 1, 2],
			["b1", 1, 60000, 30, "A区", 5, 6, 1, 2],
		],
		columns=[
			"building_key",
			"lookalike_id",
			"Price_yen",
			"area_m2",
			"municipality",
			"age_years",
			"walk_min_nearest",
			"n_rooms",
			"stories_above",
		],
	)


def test_same_building_comps_counts_pool():
    result = same_building_comps(make_val(), 1)
    assert isinstance(result, dict)
    assert result["n"] == 4      # rows 0, 2, 3, 5


def test_same_building_comps_singleton_building_returns_none():
	assert same_building_comps(make_val(), 4) is None


def test_twin_of_queried_row_is_excluded():
	result = same_building_comps(make_val(), 0)
	assert result["n"] == 3


def test_median_is_scaled_to_query_area():
	result = same_building_comps(make_val(), 0)
	assert result["median"] == 90000


def test_result_keys():
	result = same_building_comps(make_val(), 1)
	assert {"n", "median", "p25", "p75", "label"}.issubset(result)
	assert not {"building_key", "jnc", "title"}.intersection(result)


def test_min_n():
	assert same_building_comps(make_val(), 1, min_n=10) is None


def test_similar_finder_unknown_municipality_returns_none():
	assert SimilarFinder(make_val()).find({"municipality": "ZZ区", "area_m2": 30}) is None


def test_similar_finder_missing_walk_column_still_finds_comps():
	val = make_val().drop(columns="walk_min_nearest")
	result = SimilarFinder(val).find({"municipality": "A区", "area_m2": 30})
	assert isinstance(result, dict)
	assert result["n"] > 0


def test_similar_finder_invalid_query_returns_none():
	finder = SimilarFinder(make_val())
	assert finder.find({"municipality": "A区", "area_m2": 0}) is None
	assert finder.find({"area_m2": 30}) is None


def test_input_dataframe_is_not_modified():
	val = make_val()
	original = val.copy(deep=True)
	same_building_comps(val, 1)
	SimilarFinder(val).find({"municipality": "A区", "area_m2": 30})
	pd.testing.assert_frame_equal(val, original)


def test_same_building_comps_excludes_twins():
    result = same_building_comps(make_val(), 0)
    assert result["n"] == 3      # rows 1, 2, 3; row 5 is row 0's twin and is excluded
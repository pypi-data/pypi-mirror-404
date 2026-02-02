import pytest
from tukan_python.query import Query
from unittest.mock import patch, MagicMock


def test_query_init():
    q = Query()
    assert q.table_name is None
    assert q.where == []
    assert q.group_by == []
    assert q.aggregate == []
    assert q.language == "en"


def test_set_table_name():
    q = Query()
    q.set_table_name("my_table")
    assert q.table_name == "my_table"


def test_set_where():
    q = Query()
    q.set_where([{"reference": "foo"}])
    assert q.where == [{"reference": "foo"}]


def test_add_date_filter():
    q = Query()
    q.add_date_filter("date", "2020-01-01", "2020-12-31")
    assert q.where == [{"reference": "date", "from": "2020-01-01", "to": "2020-12-31"}]
    q.add_date_filter("date2", "2021-01-01")
    assert len(q.where) == 2


def test_add_numeric_filter():
    q = Query()
    q.add_numeric_filter("ref", lte=10)
    assert q.where == [{"reference": "ref", "lte": 10}]

    with pytest.raises(ValueError):
        q.add_numeric_filter("ref3")


def test_validate_numeric_filter():
    q = Query()
    with pytest.raises(ValueError):
        q.validate_numeric_filter(None, eq=1, gte=2)

    q.validate_numeric_filter(eq=1)


def test_add_standard_filter():
    q = Query()
    q.add_standard_filter("ref", ["A", "B"])
    assert q.where == [{"reference": "ref", "value": ["A", "B"]}]


def test_set_group_by():
    q = Query()
    q.set_group_by([{"reference": "foo"}])
    assert q.group_by == [{"reference": "foo"}]


def test_add_non_date_reference_to_group_by():
    q = Query()
    q.add_non_date_reference_to_group_by("bar")
    assert q.group_by == [{"reference": "bar"}]


def test_add_date_reference_to_group_by():
    q = Query()
    q.add_date_reference_to_group_by("baz", "monthly")
    assert q.group_by == [{"reference": "baz", "level": "monthly"}]

    with pytest.raises(ValueError):
        q.add_date_reference_to_group_by("baz", "invalid")


def test_validate_date_filter():
    q = Query()
    with pytest.raises(ValueError):
        q.validate_date_filter("invalid")

    q.validate_date_filter("yearly")


def test_aggregate_methods():
    q = Query()
    q.set_aggregate([{"indicator": "foo", "operations": ["sum"]}])
    assert q.aggregate == [{"indicator": "foo", "operations": ["sum"]}]


def test_add_aggregate():
    q = Query()
    q.add_aggregate("bar", ["avg"])
    assert q.aggregate == [{"indicator": "bar", "operations": ["avg"]}]

    with pytest.raises(ValueError):
        q.add_aggregate("baz", [])


def test_validate_aggregate():
    q = Query()
    with pytest.raises(ValueError):
        q.validate_aggregate(["invalid"])

    q.validate_aggregate(["sum", "avg"])


def test_set_language():
    q = Query()
    q.set_language("es")
    assert q.language == "es"


def test_get_select():
    q = Query()
    q.table_name = "my_table"
    q.aggregate = [{"indicator": "foo", "operations": ["sum"]}]
    assert q.get_select() == [{"table": "my_table", "indicators": ["foo"]}]


def test_get_iterate():
    q = Query()
    q.aggregate = [{"indicator": "foo", "operations": ["sum"]}]
    assert q.get_iterate() == [
        {"group_by": [], "aggregate": [{"indicator": "foo", "operations": ["sum"]}]}
    ]


def test_str_and_request_payload():
    q = Query()
    q.table_name = "my_table"
    q.where = [{"reference": "foo"}]
    q.group_by = [{"reference": "bar"}]
    q.aggregate = [{"indicator": "baz", "operations": ["sum"]}]
    q.language = "es"
    payload = q.__request_payload__()
    assert payload["select"] == [{"table": "my_table", "indicators": ["baz"]}]
    assert payload["where"] == [{"reference": "foo"}]
    assert payload["iterate"] == [
        {
            "group_by": [{"reference": "bar"}],
            "aggregate": [{"indicator": "baz", "operations": ["sum"]}],
        }
    ]
    assert payload["language"] == "es"
    assert str(q) == str(payload)


def test_create_identity_query_for_table():
    q = Query()
    q.create_identity_query_for_table("mex_cnbv_cb_orig_by_gender_monthly", "en")
    assert q.table_name == "mex_cnbv_cb_orig_by_gender_monthly"
    assert q.where == []
    expected_aggregate = [
        {"indicator": "05451c0b6d5ea78", "operations": ["identity"]},
        {"indicator": "78256b18c54451f", "operations": ["identity"]},
        {"indicator": "b577c6dfc51ebef", "operations": ["identity"]},
    ]
    assert q.aggregate == expected_aggregate


def test_create_identity_query_for_table_with_date_filters():
    q = Query()
    q.create_identity_query_for_table_with_date_filters(
        "mex_cnbv_cb_orig_by_gender_monthly", "en", "2020-01-01", "2020-12-31"
    )
    where = q.where
    assert len(where) == 2
    assert where[0]["to"] == "2020-12-31"


def test_all_dt_references_for_table():
    # No need.
    pass


def test_set_identity_aggregate_for_indicators():
    q = Query()
    q.all_indicators_for_table = MagicMock(return_value=["a", "b"])
    q.add_aggregate = MagicMock()
    q.set_identity_aggregate_for_indicators("table1")

    assert len(q.aggregate) == 2


def test_set_groupby_for_all_columns():
    q = Query()
    q.set_groupby_for_all_columns("mex_cnbv_cb_orig_by_gender_monthly")
    assert len(q.group_by) == 8


def test_all_dt_references_for_table():
    # No need to test
    pass


def test_all_indicators_for_table():
    q = Query()
    ans = q.all_indicators_for_table("mex_cnbv_cb_orig_by_gender_monthly")
    assert isinstance(ans, list)

    expected_ans = {"05451c0b6d5ea78", "78256b18c54451f", "b577c6dfc51ebef"}
    assert {*ans} == expected_ans


def test_save_query():
    # No need to test
    pass

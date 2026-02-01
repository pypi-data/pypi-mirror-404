"""Tests for pandas_utils module."""

from __future__ import annotations

import re
import site
from pathlib import Path

import numpy as np
import pandas as pd

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils import pandas_utils as pu  # noqa: E402


def test_add_and_remove_from_frame():
    """Rows are replaced/removed appropriately."""
    base = pd.DataFrame({"val": [1, 2]}, index=["a", "b"])
    to_add = pd.DataFrame({"val": [3]}, index=["b"])
    to_drop = pd.DataFrame(index=["a"])
    result = pu.add_and_remove_from_frame(base, to_add=to_add, to_drop=to_drop)
    assert list(result.index) == ["b"]
    assert result.loc["b", "val"] == 3


def test_filter_rows_from_frame():
    """Rows present in new_frame are filtered out of orig_frame."""
    orig = pd.DataFrame({"id": [1, 2], "val": [10, 20]})
    new = pd.DataFrame({"id": [2], "val": [99]})
    result = pu.filter_rows_from_frame(orig, new, columns="id")
    assert result["id"].tolist() == [1]


def test_replace_rows_from_frame():
    """Rows are replaced based on column key."""
    orig = pd.DataFrame({"id": [1, 2], "val": [10, 20]})
    new = pd.DataFrame({"id": [2], "val": [99]})
    result = pu.replace_rows_from_frame(orig, new, columns="id")
    assert set(result["id"]) == {1, 2}
    assert result.loc[result["id"] == 2, "val"].iloc[0] == 99


def test_get_first_value_with_query():
    """get_first_value respects query and optional default."""
    frame = pd.DataFrame({"id": [1, 2], "val": [10, 20]})
    assert pu.get_first_value(frame, "val", query="id == 2") == 20
    assert np.isnan(pu.get_first_value(frame.iloc[0:0], "val"))
    assert pu.get_first_value(frame.iloc[0:0], "val", optional_value="x") == "x"


def test_frame_regex_column_reorder():
    """Columns are reordered according to regex filters."""
    frame = pd.DataFrame(columns=["alpha", "beta", "gamma"])
    reordered = pu.frame_regex_column_reorder(
        frame, r"^g", r"^a", unmatched_at_end=True
    )
    assert reordered.columns.tolist() == ["gamma", "alpha", "beta"]


def test_ordered_list_of_columns_with_regex():
    """ordered_list_of_columns returns matches respecting order and uniqueness."""
    frame = pd.DataFrame(columns=["foo1", "foo2", "bar"])
    cols = pu.ordered_list_of_columns(frame, [re.compile(r"foo"), "bar"])
    assert cols == ["foo1", "foo2", "bar"]


def test_stringify_dataframe_and_markdown(monkeypatch):
    """stringify_dataframe formats numbers and dates and markdown renders."""
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "count": [1000, None],
            "amount": [1234.5, 67.8],
        }
    )
    stringified = pu.stringify_dataframe(df, float_precision={"amount": 1})
    assert stringified["count"].iloc[0] == "1,000"
    assert stringified["amount"].iloc[0] == "1,234.5"
    # Monkeypatch to avoid tabulate dependency in pandas to_markdown
    monkeypatch.setattr(pd.DataFrame, "to_markdown", lambda self, **kwargs: "| date |")
    md = pu.dataframe_to_markdown(stringified, stringify=False)
    assert "| date" in md


def test_create_rolled_up_frame_simple():
    """create_rolled_up_frame produces expected totals."""
    frame = pd.DataFrame(
        {
            "cat": ["A", "A", "B"],
            "value": [1, 2, 3],
            "prop": ["x", "y", "z"],
        }
    )
    rolled = pu.create_rolled_up_frame(
        frame,
        categories=["cat"],
        sum_columns_or_regex=["value"],
        property_columns_or_regex=["prop"],
        property_category="cat",
        remove_blank_cat=True,
    )
    # Expect Total row and per-category rows
    assert set(rolled["id"]) == {"Total", "A", "B"}
    assert rolled.loc[rolled["id"] == "A", "value"].iloc[0] == 3
    assert rolled.loc[rolled["id"] == "B", "value"].iloc[0] == 3

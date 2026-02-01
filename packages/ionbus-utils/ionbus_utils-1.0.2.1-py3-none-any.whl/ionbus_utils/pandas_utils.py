"""Pandas utilities"""

from __future__ import annotations

# pylint: disable=ungrouped-imports,wrong-import-order

import re

import numpy as np
import pandas as pd

from typing import Optional, Any

from ionbus_utils.general import filter_string_rep_of_list
from ionbus_utils.logging_utils import logger

TOTAL_ID = "_total_id___"


def add_and_remove_from_frame(
    starting: pd.DataFrame,
    to_add: Optional[pd.DataFrame] = None,
    to_drop: Optional[pd.DataFrame] = None,
    to_sort: bool = False,
) -> pd.DataFrame:
    """Returns updated frame by adding/updating to_add and removing
    to_del. This assumes the rows can be uniquely identified by their
    index."""
    if to_add is None:
        to_add = pd.DataFrame()
    if to_drop is None:
        to_drop = pd.DataFrame()
    # To keep the frame up to date, we want to first drop from _results
    # all indices in to_add and to_del (after assuring that they are in
    # _results) and then concat that updated frame with the to_add
    # frame.
    keys_to_drop = (set(to_drop.index) | set(to_add.index)).intersection(
        set(starting.index)
    )
    ret_frame = pd.concat(
        [
            starting.drop(keys_to_drop),  # type: ignore
            to_add,  # type: ignore
        ]
    )
    if to_sort:
        return ret_frame.sort_index()
    return ret_frame


def filter_rows_from_frame(
    orig_frame: pd.DataFrame,
    new_frame: pd.DataFrame,
    columns: str | list[str],
) -> pd.DataFrame:
    """Filters out rows in new_frame that are in orig_frame based on
    columns provided.

    This function assumes that the columns provided are sufficient for
    describing unique rows.  If a subset of the columns provided are given,
    the final data frame will likely be shorter than expected."""
    if new_frame.empty or orig_frame.empty:
        return orig_frame
    if isinstance(columns, str):
        columns = [columns]
    new = {tuple(x) for x in new_frame[columns].values}
    return orig_frame[
        orig_frame[columns].apply(lambda x: tuple(x.values) not in new, axis=1)
    ]


def replace_rows_from_frame(
    orig_frame: pd.DataFrame,
    new_frame: pd.DataFrame,
    columns: str | list[str],
) -> pd.DataFrame:
    """Replaces rows in orig_frame with those in new_frame based on
    columns provided.

    This function assumes that the columns provided are sufficient for
    describing unique rows.  If a subset of the columns provided are given,
    the final data frame will likely be shorter than expected."""
    if new_frame.empty:
        return orig_frame
    if orig_frame.empty:
        return new_frame
    return pd.concat(
        [
            filter_rows_from_frame(orig_frame, new_frame, columns),
            new_frame,
        ]
    )


def get_first_value(
    frame: pd.DataFrame,
    col: str,
    query: Optional[str] = None,
    optional_value: Optional[Any] = None,
) -> Any:
    """Gets the first instance of a particular column from a frame using an
    optional query.
    This is meant to be used if we expect exactly one instance or the frame is
    sorted and we want the first instance.
    If this fails to get a value, optional_value (if provided) or np.nan
    will be returned"""
    if frame.empty:
        return optional_value if optional_value is not None else np.nan
    if query:
        frame = frame.query(query)
    if frame.empty:
        return optional_value if optional_value is not None else np.nan
    if col not in frame.columns:
        logger.warning(f"column '{col}' not found in frame.")
        return optional_value if optional_value is not None else np.nan
    return frame[col].iloc[0]


def frame_regex_column_reorder(
    frame: pd.DataFrame,
    *args: list | str | re.Pattern,
    ignore_case: bool = True,
    full_match: bool = False,
    unmatched_at_end: bool = False,
) -> pd.DataFrame:
    """Reorders the columns based on list of strings and regex
    passed in. This function assumes that the columns is NOT a multi-index.

    This uses ionbus_utils.general.filter_string_rep_of_list.  Please read
    that function readme for full spec"""
    new_columns = filter_string_rep_of_list(
        frame.columns,
        *args,  # type: ignore
        ignore_case=ignore_case,
        full_match=full_match,
        unmatched_at_end=unmatched_at_end,
    )
    return frame[new_columns]


def ordered_list_of_columns(
    frame: pd.DataFrame,
    column_names_or_regex: Optional[list[str | re.Pattern]],
) -> list:
    """Takes a list of strings or regex and returns list of columns in the
    frame.
    Order will be same as column_names_or_regex.  If there are multiple
    matches for a regex, the order of the columns in the frame will be
    respected.
    Duplicates will e dropped.
    """
    if column_names_or_regex is None:
        return []
    ret_list = []
    # sor = String Or Regex
    for sor in column_names_or_regex:
        if isinstance(sor, str):
            if sor in frame.columns and sor not in ret_list:
                ret_list.append(sor)
            continue
        to_extend = [x for x in frame.columns if sor.search(x)]
        for column in to_extend:
            if column not in ret_list:
                ret_list.append(column)
    return ret_list


def _generate_id_and_category(
    row,
    columns,
    name_col,
    set_name: bool | str = False,
    remove_blank_cat: bool = True,
) -> pd.Series:
    """create ID and category information"""
    cat = ""
    last = set_name
    prev_cat = ""
    for col in columns:
        value = row[col]
        if pd.isnull(value):
            break
        last = col
        prev_cat = cat
        if cat:
            if value or not remove_blank_cat:
                cat += f".{value}"
        else:
            cat = value
    if set_name:
        return pd.Series((row[last], prev_cat or set_name, cat))
    id_var = f"{cat}.{row[name_col]}"
    return pd.Series((cat, id_var))


def _rolled_up_sum_frame(
    frame,
    sum_columns: list[str],
    property_columns: Optional[list[str]] = None,
    copy_properties: bool = False,
):
    """Calculate sum of requested rows.  Expected to be used in a groupby."""
    ret_dict = {}
    for col in sum_columns:
        ret_dict[col] = frame[col].sum()
    if copy_properties and property_columns is not None:
        for col in property_columns:
            ret_dict[col] = (
                frame[col].iloc[0] if col in frame.columns else np.nan
            )
    return pd.Series(ret_dict)


def create_rolled_up_frame(
    frame: pd.DataFrame,
    categories: list,
    sum_columns_or_regex: list[str | re.Pattern],
    property_columns_or_regex: Optional[list[str | re.Pattern]] = None,
    property_category: Optional[str] = None,
    remove_blank_cat: bool = True,
    blank_columns_to_add: Optional[list] = None,
) -> pd.DataFrame:
    """Create rolled up frame with categories to be displayed with tools
    like JQX Tree Grid."""
    if frame.empty:
        # we've got nothing to roll up
        return pd.DataFrame()
    sum_columns = ordered_list_of_columns(frame, sum_columns_or_regex)
    property_columns = ordered_list_of_columns(frame, property_columns_or_regex)
    frame = frame.copy()
    frame["_all"] = "all"
    top = (
        frame.groupby("_all")
        .apply(lambda x: _rolled_up_sum_frame(x, sum_columns, property_columns))
        .reset_index(drop=True)
    )
    top["category"] = np.nan
    top["id"] = "Total"
    top["full_name"] = "Total"
    if blank_columns_to_add is None:
        blank_columns_to_add = []
    else:
        for col in blank_columns_to_add:
            top[col] = np.nan
    copy_properties = False
    for idx, cat in enumerate(categories):
        if cat == property_category:
            copy_properties = True
        gb_cols = categories[0 : idx + 1]
        summ = (
            frame.groupby(gb_cols)
            .apply(
                lambda x: _rolled_up_sum_frame(
                    x,
                    sum_columns,
                    property_columns,
                    copy_properties,
                )
            )
            .reset_index(drop=False)
        )
        # pylint: disable=cell-var-from-loop
        summ[["full_name", "category", "id"]] = summ.apply(
            lambda x: _generate_id_and_category(
                x, gb_cols, "full_name", "Total", remove_blank_cat
            ),
            axis=1,
        )
        if remove_blank_cat:
            summ.query("category != id", inplace=True)
        top = pd.concat([top, summ])
    top.sort_values(categories, inplace=True)
    new_sum_columns = ordered_list_of_columns(top, sum_columns_or_regex)
    return frame_regex_column_reorder(
        top.reset_index(drop=True),
        *(["full_name", "category", "id"] + property_columns + new_sum_columns),
        unmatched_at_end=False,
    )


def get_parent_id(
    row: pd.Series,
    cols: list,
    add_total_line: bool = True,
) -> str | None:
    """
    Generate a parent ID for a row based on specified columns.

    :param row: Series representing a row in the DataFrame
    :param cols: List of column names to use for generating the parent ID
    :return: Parent ID as a string or None if all values are NaN
    """
    values = [
        str(x) if not pd.isnull(x := row[col]) else "(NONE)"  # type: ignore
        for col in cols
    ]
    return (
        "...".join(values) if values else (TOTAL_ID if add_total_line else None)
    )


def rolled_up_frame(
    orig_frame,
    orig_groupby_cols: list[str],
    agg_cols: list[str],
    base_frame_name_col: str,
    add_total_line: bool = True,
    show_grouping_columns: bool = True,
    missing_name_override: dict[str, str] | None = None,
    extra_columns: list[str] | None = None,
    name_col: str = "display_name",
    keep_other_cols: bool | list = False,
):
    """
    Roll up a DataFrame by specified columns and aggregation dictionary.

    orig_frame:            DataFrame to roll up
    orig_groupby_cols:     List of columns to group by
    agg_cols:              List of columns to aggregate
    base_frame_name_col:   Column in orig_frame to use as the name
    add_total_line:        Whether to add a total line at the end (default: True)
    show_grouping_columns: Whether to include grouping columns in the output (default: True)
    missing_name_override: Dictionary to override names for missing values (default: None)
    extra_columns:         Additional columns of original frame to include in the output (default: None)
    name_col:              Name of the column to use for display names (default: "display_name")
    keep_other_cols:       Whether to keep other columns not specified in agg_cols (default: False).

    Returns rolled up DataFrame with hierarchical structure.
    """  # noqa: E501
    if len(orig_groupby_cols) < 2:
        print(orig_groupby_cols)
        raise ValueError("groupby_cols must be at least 2")
    agg_dict = {
        x: "sum" if idx else ("sum", "count") for idx, x in enumerate(agg_cols)
    }
    groupby_cols = orig_groupby_cols[:]
    frame = orig_frame.copy().reset_index(drop=True)
    frame["tg_key"] = frame.index.map(lambda x: f"idx_{x:05d}")
    frame["tg_parent"] = frame.apply(
        lambda x: get_parent_id(x, groupby_cols), axis=1
    )
    frame[name_col] = frame[base_frame_name_col]
    print(frame.tg_parent.iloc[0])
    frame["_level"] = len(groupby_cols) + 1
    ret_frames = [frame]
    while groupby_cols:
        level = len(groupby_cols)
        col = groupby_cols[-1]
        subset = (
            orig_frame.groupby(groupby_cols, dropna=False)
            .agg(agg_dict)
            .reset_index()
        )
        subset.columns = [
            x[0] if x[1] != "count" else "num_rows" for x in subset.columns
        ]
        subset["tg_key"] = subset.apply(
            lambda x: get_parent_id(x, groupby_cols), axis=1
        )
        subset["tg_parent"] = subset.apply(
            lambda x: get_parent_id(
                x, groupby_cols[:-1], add_total_line=add_total_line
            ),
            axis=1,
        )
        subset[name_col] = subset[col]
        if missing_name_override and (
            override := missing_name_override.get(col)
        ):
            subset.loc[pd.isnull(subset[name_col]), name_col] = override
        groupby_cols.pop()
        subset["_level"] = level
        ret_frames.append(subset)
    big_frame = pd.concat(ret_frames, ignore_index=True)
    big_frame.loc[pd.isna(big_frame["tg_parent"]), "tg_parent"] = None
    big_frame = big_frame.sort_values(
        ["tg_parent", base_frame_name_col, "tg_key"],
        na_position="first",
    )
    front = (
        [name_col, "tg_parent", "tg_key", "_level"]
        + (orig_groupby_cols if show_grouping_columns else [])
        + agg_cols
    )
    if add_total_line:
        total_frame = pd.DataFrame([{x: orig_frame[x].sum() for x in agg_cols}])
        total_frame[name_col] = "Total"
        total_frame["tg_key"] = TOTAL_ID
        total_frame["tg_parent"] = None
        total_frame["_level"] = 0
        big_frame = pd.concat([total_frame, big_frame], ignore_index=True)
    all_cols = front
    if keep_other_cols:
        if keep_other_cols is True:
            keep_other_cols = list(orig_frame.columns)
        all_cols.extend(
            [
                x
                for x in big_frame.columns
                if x not in front and x in keep_other_cols
            ]
        )
    big_frame = big_frame[all_cols]
    if not add_total_line:
        big_frame["_level"] -= 1
    return big_frame


def stringify_dataframe(
    df: pd.DataFrame,
    float_precision: dict[str, int] | None = None,
    int_no_commas: set[str] | None = None,
) -> pd.DataFrame:
    """
    Convert all DataFrame columns to formatted strings. Often used by
    dataframe_to_markdown().

    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame to stringify.
    float_precision : dict[str, int] | None
        Optional dictionary mapping column names to decimal precision.
        Default precision is 0 for all float columns.
    int_no_commas : set[str] | None
        Optional set of integer column names to format without commas.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with all columns converted to strings.

    Examples
    --------
    >>> df = pd.DataFrame({
    ...     'date': pd.to_datetime(['2024-01-01', '2024-01-02']),
    ...     'timestamp': pd.to_datetime(['2024-01-01 14:30:00']),
    ...     'count': [1000, 2000],
    ...     'amount': [1234.56, 7890.12]
    ... })
    >>> result = stringify_dataframe(df, float_precision={'amount': 2})
    """
    float_precision = float_precision or {}
    int_no_commas = int_no_commas or set()
    result_df = df.copy()

    for col in result_df.columns:
        # Handle datetime columns
        if pd.api.types.is_datetime64_any_dtype(result_df[col]):
            # Check if all times are midnight (00:00:00)
            non_null = result_df[col].dropna()
            if len(non_null) > 0:
                is_date_only = all(
                    ts.hour == 0 and ts.minute == 0 and ts.second == 0
                    for ts in non_null
                )
                if is_date_only:
                    result_df[col] = result_df[col].dt.strftime(  # type: ignore
                        "%Y-%m-%d"
                    )
                else:
                    result_df[col] = result_df[col].dt.strftime(  # type: ignore
                        "%Y-%m-%d %H:%M:%S"
                    )
            else:
                result_df[col] = result_df[col].apply(
                    lambda x: "" if pd.isna(x) else str(x)
                )

        # Handle integer columns
        elif pd.api.types.is_integer_dtype(result_df[col]):
            if col in int_no_commas:
                result_df[col] = result_df[col].apply(
                    lambda x: f"{x}" if pd.notna(x) else ""
                )
            else:
                result_df[col] = result_df[col].apply(
                    lambda x: f"{x:,}" if pd.notna(x) else ""
                )

        # Handle float columns
        elif pd.api.types.is_float_dtype(result_df[col]):
            precision = float_precision.get(col, 0)
            format_str = f"{{:,.{precision}f}}"
            result_df[col] = result_df[col].apply(
                lambda x: format_str.format(x) if pd.notna(x) else ""
            )

        # Convert any remaining types to string
        else:
            result_df[col] = result_df[col].astype(str)

    return result_df


def dataframe_to_markdown(
    df: pd.DataFrame,
    float_precision: dict[str, int] | None = None,
    int_no_commas: set[str] | None = None,
    colalign_override: dict[str, str] | None = None,
    stringify: bool = True,
    index: bool = False,
    disable_numparse: bool = True,
) -> str:
    """
    Convert DataFrame to markdown with automatic column alignment.

    Requires the `tabulate` package be installed (`conda install tabulate`)

    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame to convert.
    float_precision : dict[str, int] | None
        Optional dictionary mapping column names to decimal precision.
        Default precision is 0 for all float columns.
    int_no_commas : set[str] | None
        Optional set of integer column names to format without commas.
    colalign_override : dict[str, str] | None
        Optional dictionary mapping column names to alignment
        ('left', 'right', 'center'). Overrides default alignment.
    stringify : bool
        Whether to stringify the DataFrame first. Default True.
    index : bool
        Whether to include the index in markdown output. Default False.
    disable_numparse : bool
        Whether to disable tabulate's number parsing to preserve
        formatted strings exactly. Default True.

    Returns
    -------
    str
        Markdown formatted string.

    Examples
    --------
    >>> df = pd.DataFrame({
    ...     'name': ['Alice', 'Bob'],
    ...     'count': [1000, 2000],
    ...     'amount': [1234.56, 7890.12]
    ... })
    >>> md = dataframe_to_markdown(
    ...     df,
    ...     float_precision={'amount': 2},
    ...     colalign_override={'name': 'center'}
    ... )
    """
    colalign_override = colalign_override or {}

    # Build colalign list based on original dtypes
    colalign = [
        colalign_override.get(
            col, "left" if str(df[col].dtype) == "object" else "right"
        )
        for col in df.columns
    ]

    # Stringify if requested
    if stringify:
        df = stringify_dataframe(df, float_precision, int_no_commas)

    return df.to_markdown(
        colalign=colalign, index=index, disable_numparse=disable_numparse
    )

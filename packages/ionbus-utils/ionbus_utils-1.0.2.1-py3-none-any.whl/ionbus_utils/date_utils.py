"""Date utilities"""

from __future__ import annotations

# cSpell: ignore fstring
# pylint: disable=W0611,C0411,logging-fstring-interpolation
import datetime as dt

import pandas as pd

from ionbus_utils.regex_utils import NON_DIGIT_RE


def yyyymmdd_to_date(string: str | None) -> dt.date | None:
    """Converts a string of format yyyyy-mm-dd to a date object.
    All punctuation/non digits are ignored if a string is passed.
    An empty string or non will have None returned"""
    return (
        dt.datetime.strptime(NON_DIGIT_RE.sub("", string), "%Y%m%d").date()
        if string
        else None
    )


def to_date(
    the_date: dt.date | dt.datetime | pd.Timestamp | str | None,
) -> dt.date | None:
    """Returns date (if date/time object) or None"""
    if not the_date:
        return None
    return pd.Timestamp(the_date).date()


def to_date_isoformat(
    the_date: dt.date | dt.datetime | pd.Timestamp | str | None,
    no_symbols: bool = False,
) -> str | None:
    """Returns date in isoformat string (if date/time object) or None"""
    if (date_obj := to_date(the_date)) is None:
        return None
    ret_val = date_obj.isoformat()
    return ret_val.replace("-", "") if no_symbols else ret_val


def first_day_of_next_month(
    the_date: dt.date | dt.datetime | pd.Timestamp | str,
) -> dt.date:
    """returns a date 1st of next month"""
    new_date = to_date(the_date)
    if not new_date:
        raise RuntimeError("Most provide valid date")
    return dt.date(
        (
            new_date.year + 1
            if new_date.month == 12  # noqa: PLR2004
            else new_date.year
        ),
        new_date.month % 12 + 1,
        1,
    )


def first_day_of_month(
    the_date: dt.date | dt.datetime | pd.Timestamp | str,
) -> dt.date:
    """returns first day of this month"""
    new_date = to_date(the_date)
    if not new_date:
        raise RuntimeError("Most provide valid date")
    return dt.date(
        new_date.year,
        new_date.month,
        1,
    )


def last_day_of_month(
    the_date: dt.date | dt.datetime | pd.Timestamp | str,
) -> dt.date:
    """returns last day of this month"""
    return first_day_of_next_month(the_date) - dt.timedelta(days=1)


# Tools for generation partition strings for different types of
# date partitions


def ensure_date_is_iso_string(
    the_date: dt.date | dt.datetime | pd.Timestamp | str | None,
) -> str | None:
    """Converts date to year-week string.  If None passed
    in, None is returned"""
    if not the_date:
        return None
    return pd.Timestamp(the_date).date().isoformat()

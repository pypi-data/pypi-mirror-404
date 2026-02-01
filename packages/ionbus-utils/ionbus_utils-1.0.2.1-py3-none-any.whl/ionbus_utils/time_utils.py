"""Useful time utilities"""

from __future__ import annotations

import datetime as dt
import re
from datetime import date, datetime, time, timedelta, tzinfo
from queue import PriorityQueue
from threading import Lock
from typing import Any, Callable, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError  # type: ignore

import numpy as np
import pandas as pd

from ionbus_utils.date_utils import to_date


nyc_timezone = None
utc_timezone = None

TimeZone: type = type(None)
_timezones_enabled = True


TimeZone = ZoneInfo
nyc_timezone = ZoneInfo("US/Eastern")
utc_timezone = ZoneInfo("UTC")

# The generic type of an object that can be converted to a datetime.
TimeType = Union[time, str, list, datetime, pd.Timestamp, int, float]
TimeZoneInput = Union[TimeZone, str, tzinfo, None]

STR_TO_TIMEZONE = {
    "ET": nyc_timezone,
    "NYC": nyc_timezone,
    "GMT": utc_timezone,
    "UTC": utc_timezone,
}

timeRE = re.compile(r"^(\d+):(\d+):?([d+\.?\d*]+)?$")  # noqa: N816


def ensure_time(  # noqa: C901
    time_obj: TimeType,
    timedelta_number_unit: str | None = None,
) -> time:
    """Converts several formats to datetime.time:
    * time, string, list of int, datetime, pt.Timestamp.

    If an integer is provided WITHOUT timedelta_number_units, then it is
    converted to  number of minutes since midnight.

    If a number is provided WITH timedelta_number_units, then it is
    converted to a timedelta and added to now and resulting time is
    returned."""
    if isinstance(time_obj, (int, float)) and timedelta_number_unit:
        kwargs = {timedelta_number_unit: time_obj}
        return (dt.datetime.now() + dt.timedelta(**kwargs)).time()
    if isinstance(time_obj, time):
        return time_obj
    if isinstance(time_obj, str):
        match = timeRE.search(time_obj)
        if not match:
            raise RuntimeError(f"{time_obj} string does not match HH:MM")
        hour = int(match.group(1))
        minutes = int(match.group(2))
        sec_str = match.group(3)
        if sec_str:
            float_seconds = float(sec_str)
            seconds = int(float_seconds)
            micro = int(float_seconds * 1e6) - seconds * 1_000_000
        else:
            seconds = 0
            micro = 0
        return time(hour, minutes, seconds, micro)
    if isinstance(time_obj, list):
        while len(time_obj) < 2:  # noqa: PLR2004
            time_obj.append(0)
        return time(*time_obj)
    if isinstance(time_obj, (datetime, pd.Timestamp)):
        return time_obj.time()
    if isinstance(time_obj, int):
        # We are going to assume that we have minutes after midnight
        if time_obj < 0 or time_obj >= 1440:  # noqa: PLR2004
            raise RuntimeError(
                f"Cannot parse int {time_obj} as minutes of the day"
            )
        hours, minutes = divmod(time_obj, 60)
        return time(hours, minutes)
    # We do not know what this is
    raise RuntimeError(
        f"Conversion not understood from {time_obj=} ({type(time_obj)})"
    )


def datetime_from_date_and_time(
    date_obj: date | datetime | pd.Timestamp | str,
    time_obj: TimeType,
    zone: TimeZoneInput = None,  # type: ignore
    timedelta_number_unit: str | None = None,
) -> datetime:
    """Creates datetime object from date and time. Uses only date from
    dateObj when datetime objects. Providing no value or None for the "zone"
    parameter will create a timezone-naive datetime."""
    date_obj_updated = to_date(date_obj)
    if date_obj_updated is None:
        raise RuntimeError(f"Unable to convert '{date_obj}' to a date.")
    time_obj = ensure_time(time_obj, timedelta_number_unit)
    return datetime.combine(
        date_obj_updated, time_obj, tzinfo=ensure_timezone_or_none(zone)
    )


def datetime_from_time_and_date_start_time(
    time_to_convert: TimeType,
    date_start_time: TimeType,
    zone: TimeZoneInput | None = None,  # type: ignore
    _now: datetime | None = None,
) -> datetime:
    """Returns a (optionally timezoned) datetime that falls on the same Trade
    Date as the start time provided.
    Use a date_start_time with a date in order to specify the TradeDate,
    otherwise it will be calculated using datetime.now().
    _now is used for testing to override datetime.now() for all calculations
    (i.e. in tests/time_tests.py)"""

    zone = ensure_timezone_or_none(zone)
    target_time = ensure_time(time_to_convert)
    start_time = ensure_time(date_start_time)

    # Find date_start_ts as the last time before now that date_start_time shows
    # up
    if isinstance(date_start_time, (datetime, pd.Timestamp)):
        if zone:
            date_start_time = date_start_time.astimezone(zone)
        date_start_ts = date_start_time
    else:
        if not _now:
            _now = datetime.now(tz=zone)
        if zone:
            _now = _now.astimezone(zone)
        date_start_ts = datetime.combine(_now.date(), start_time, tzinfo=zone)
        if date_start_ts > _now:
            date_start_ts -= timedelta(days=1)
    target_ts = datetime.combine(date_start_ts.date(), target_time, tzinfo=zone)
    # Make sure target_ts is after date_start_ts
    if target_ts < date_start_ts:
        target_ts += timedelta(days=1)
    return target_ts


def is_timezone(zone_obj: Any) -> bool:
    """Checks if the specified object is a TimeZone. Depending on which modules
    are imported, this could include zoneinfo.ZoneInfo."""
    return isinstance(zone_obj, TimeZone)


def ensure_timezone_or_none(zone: TimeZoneInput) -> TimeZone | None:  # type: ignore
    """Returns a ZoneInfo object based on the timezone code.
    In Python 3.8, currently only supports ET, NYC, GMT, and UTC.
    Python >= 3.9 will return ZoneInfo objects for other strings as well.
    Any other strings will throw
    an error. Default is NYC."""
    if is_timezone(zone) or zone is None:
        return zone
    result = STR_TO_TIMEZONE.get((zone or "NYC").upper())  # type: ignore
    if not result:
        if ZoneInfo is not None:
            try:
                return ZoneInfo(zone)
            except ZoneInfoNotFoundError:
                pass
    return result


def ensure_timezone(zone: TimeZoneInput) -> TimeZone:  # type: ignore
    """Ensures that a timezone is returned.  If None is passed in,
    defaults to NYC timezone.

    This function works exactly as ensure_timezone_or_none
    except that it does not allow None as an input."""
    zone = ensure_timezone_or_none(zone)
    if zone is None:
        raise RuntimeError(f"Time zone not found for string {zone}.")
    return zone  # type: ignore


def now_nyc() -> datetime:
    """Get now timezoned on Eastern US"""
    return datetime.now(tz=nyc_timezone)


def now_utc() -> datetime:
    """Get now UTC-timezoned"""
    return datetime.now(tz=utc_timezone)


def minutes_offset(
    timestamp: pd.Timestamp | np.datetime64 | dt.datetime,
    rounding: int,
) -> int:
    """Calculates number of minutes to round up to next interval.
    NOTE: rounding MUST be an integer divisor of 60"""
    left_over = pd.Timestamp(timestamp).minute % rounding
    return rounding - left_over if left_over else 0


def round_timestamp_up(
    timestamp: pd.Timestamp | np.datetime64 | dt.datetime,
    rounding: int,
) -> pd.Timestamp | np.datetime64 | dt.datetime:
    """Returns timestamp rounded up.  This function assumes:
    * rounding is an integer divisor of 60
    * timestamp has no seconds or microseconds
    """
    offset = minutes_offset(timestamp, rounding)
    if isinstance(timestamp, np.datetime64):
        return timestamp + np.timedelta64(offset, "m")
    return timestamp + dt.timedelta(minutes=offset)


class TimePriorityQueue:
    """Implement a time queue using priority queue"""

    now_func: Callable
    _queue: PriorityQueue
    _lock: Lock

    def __init__(
        self,
        use_timezones: bool = False,
        now_func: Callable | None = None,
    ):
        if now_func:
            self.now_func = now_func
        elif use_timezones:
            self.now_func = now_nyc
        else:
            self.now_func = dt.datetime.now
        self._queue = PriorityQueue()
        self._lock = Lock()
        self._index = 0

    def empty(self) -> bool:
        """Returns true if empty"""
        with self._lock:
            return self._queue.empty()

    def __len__(self):
        with self._lock:
            return self._queue.qsize()

    def add(self, time_obj: dt.datetime | dt.timedelta, obj: Any) -> None:
        """Adds element to time queue"""
        if isinstance(time_obj, dt.timedelta):
            time_obj = self.now_func() + time_obj
        with self._lock:
            # multiple adds at the same time will be returned in
            # order of addition.
            #
            # NOTE: We are adding the index so that the object added to the
            # queue is always sortable - if there are two times that are
            # identical, the tuple of index and object is easily sortable.
            #
            # In the future, we could add an option to TimeQueue that
            # allows it to fall back to the sortability of obj, but that
            # will never be the default.
            self._index += 1
            self._queue.put((time_obj, (self._index, obj)))

    def next_time(self) -> dt.datetime | None:
        """Returns earliest time if queue not empty, else None.
        This call does NOT modify the underlying queue."""
        with self._lock:
            return self._unlocked_next_time()

    def time_until_next_item(self) -> float | None:
        """Returns float number of seconds (negative if past due) of time
        until earliest item in queue.
        This call does NOT modify the underlying queue."""
        with self._lock:
            time_obj = self._unlocked_next_time()
            if time_obj is None:
                return time_obj
            return (time_obj - self.now_func()).total_seconds()

    def next_item(self) -> tuple[dt.datetime, Any] | None:
        """Returns next pair if not empty, else None.
        This call can modify the underlying queue."""
        with self._lock:
            if self._queue.empty():
                return None
            time_obj, pair = self._queue.get()
            return time_obj, pair[1]

    def next_ready_item(
        self,
        extra: float = 0,
    ) -> tuple[dt.datetime, Any] | None:
        """Returns next pair IF it is time and not empty, else None.
        If you want to get entries that might be ready in the next N seconds,
        set extra to N.
        This call can modify the underlying queue."""
        now = self.now_func() - dt.timedelta(seconds=extra)
        with self._lock:
            # we're empty, there's nothing to return
            if self._queue.empty():
                return None
            # Ok. we're not empty.  Are we ready to pull of next time?
            if now < self._queue.queue[0][0]:
                # Nope.  Too soon
                return None
            time_obj, pair = self._queue.get()
            return time_obj, pair[1]

    def _unlocked_next_time(self) -> dt.datetime | None:
        """This function SHOULD NOT BE CALLED from outside the class"""
        if self._queue.empty():
            return None
        return self._queue.queue[0][0]


if __name__ == "__main__":
    print(ensure_timezone_or_none("America/New_York"))

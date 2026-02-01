# time_utils Documentation

## Introduction

The core_utils [time_utils.py](time_utils.py) module contains many functions to manage working with `datetime` or `Timestamp` objects.

### Functions in time_utils

`ensure_time`

Many functions in time_utils accept a `TimeType` object. This is a special type that can be provided in a number of different forms, all of which will be converted to `datetime.time` objects. The `ensure_time` function is used to convert a `TimeType` to a usable `datetime.time`.

- `str` objects: Interprets the string as a 24-hr "HH:MM" or "HH:MM:SS" time

```python
ensure_time("9:15")
# Output | 09:15:00

ensure_time("16:10:30")
# Output | 16:10:30
```

- `list` objects: Interprets the list as 24-hr [hour, minute, (second)]

```python
ensure_time([9, 15])
# Output | 09:15:00

ensure_time([9, 15, 30])
# Output | 09:15:30
```

- `datetime.time` objects will not be changed

```python
ensure_time(time(16, 45))
# Output | 16:45:00
```

- `datetime.datetime` and `pandas.Timestamp` objects: Uses the object's .time()

```python
ensure_time(datetime(2024, 7, 24, 8, 30))
# Output | 08:30:00

ensure_time(pd.Timestamp("2024-07-24 08:30:00"))
# Output | 08:30:00
```

- `int` objects (no `timedelta_number_unit`): Interprets the time as "minutes after midnight".

```python
ensure_time(0)
# Output | 00:00:00

ensure_time(30)
# Output | 00:30:00

ensure_time(1200)
# Output | 20:00:00
```

- `int` and `float` objects (with `timedelta_number_unit`): Interprets the time as N time units after now. The time unit is specified via `timedelta_number_unit` and can be any supported unit: days, hours, minutes, seconds, etc. This is mostly useful for testing purposes.

```python
# The following functions are being run at 2024-07-24 10:00:00

ensure_time(0, timedelta_number_unit="seconds")
# Output | 10:00:00

ensure_time(30, timedelta_number_unit="minutes")
# Output | 10:30:00

ensure_time(4.5, timedelta_number_unit="hours")
# Output | 12:30:00
```

`datetime_from_date_and_time`

This function is used for combining a date with a generic time input (one that can be interpreted by [`ensure_time`](#functions-in-time_utils)), such as when creating datetimes from config variables. The `date_obj` provided can either be a `datetime.date`, or a `datetime.datetime` or `pandas.Timestamp` in which case only the date will be used. In all cases, only the time of the `time_obj` will be used.

Examples:

```python
from core_utils.time_utils import datetime_from_date_and_time
from datetime import date, time, datetime

today = date(2024, 7, 23)  # 2024-07-23
datetime_from_date_and_time(today, "08:00")
# Output | 2024-07-23 08:00:00

datetime_from_date_and_time(today, time(10, 30))
# Output | 2024-07-23 10:30:00

datetime_from_date_and_time(today, datetime(2000, 4, 15, 16, 0))
# Output | 2024-07-23 16:00:00

datetime_from_date_and_time(today, "08:00", zone="NYC")
# Output | 2024-07-23 08:00:00-04:00

datetime_from_date_and_time(today, "08:00", zone="UTC")
# Output | 2024-07-23 08:00:00+00:00
```

`now_nyc` and `now_utc`

Returns the time right now in the Eastern Time Zone and UTC timezone respectively. Note that comparisons will work correctly with datetimes of a different timezones - so using `now_nyc()` or `now_utc()` is appropriate even when running in another time zone.

`nyc_timezone` and `utc_timezone`

These global variables are timezone objects representing the NY/ET timezone and the UTC/GMT timezone. It is preferred to use this over creating custom timezones for version compatability. (See [Working with Timezones](#working-with-timezones)).

`ensure_timezone_or_none` and `ensure_timezone`

Many functions in time_utils accept a "zone" parameter, which can be any of the following types. The `ensure_timezone_or_none` function is used to convert these to usable timezones.  `ensure_timezone` works just like `ensure_timezone_or_none` except that it cannot return None (it will throw)

- `None` returns `None` directly, and will result in non-timezoned datetimes.
- A `str` input will return the timezone associated with that string.
    - "ET" and "NYC" will return the nyc_timezone object.
    - "UTC" and "GMT" will return the utc_timezone object.
    - For python >= 3.9, any allowed ZoneInfo name will work as well.
- A `TimeZone` input will return the timezone provided (such as if nyc_timezone is passed to the function).

Examples:

```python
from core_utils.time_utils import ensure_timezone_or_none, nyc_timezone

ensure_timezone_or_none(None)
# Output | None

ensure_timezone_or_none("ET")
# Output | nyc_timezone

ensure_timezone_or_none("UTC")
# Output | utc_timezone

ensure_timezone_or_none(nyc_timezone)
# Output | nyc_timezone
```

`datetime_from_time_and_date_start_time`

Most systems in the Eastern time zone will consider a single "Trade Day" to start at "18:00". This function is used for determining a datetime based off of a `date_start_time`, which defines the time at what time the "Trade Date" rolls over to the next day. If a `datetime` or `Timestamp` is provided for `date_start_time`, the `date_start` rollover will be exactly that `date_start_time`. Otherwise, `date_start` will be calculated based on the current time, `datetime.now()`, as the most recent time `date_start_time` occurred before `now`.

Examples:

```python
from core_utils.time_utils import datetime_from_time_and_date_start_time
from datetime import datetime

# Function is being run at 2024-07-23 15:00:00
datetime_from_time_and_date_start_time("03:00", "18:00")
# Since now is before the date_start_time, 3:00 must be referring to earlier
# today.
# Output | 2024-07-23 03:00:00

# Function is being run at 2024-07-23 20:00:00
datetime_from_time_and_date_start_time("03:00", "18:00")
# Since now is after the date_start_time, 3:00 must be referring to tomorrow.
# Output | 2024-07-24 03:00:00

# Function is being run at 2024-07-23 15:00:00
datetime_from_time_and_date_start_time("19:00", "18:00")
# Since now is after the date_start_time, 19:00 must be referring to today's
# Trade Date, but yesterday's actual (ET) date.
# Output | 2024-07-22 19:00:00
```

`round_timestamp_up`

Rounds the specified time up to the nearest N minutes of the hour. The N must be a divisor of 60 minutes (1, 5, 15, ... among others). This is useful for calculating the ceiling of the time in N-minute chunks, such as when converting 1-minute to 5-minute bar data. This function accepts datetimes (from datetime), Timestamps (from pandas), and datetime64s (from numpy), but expects a time without seconds, milliseconds, etc.

Examples:

```python
from core_utils.time_utils import round_timestamp_up

round_timestamp_up(dt.datetime(2024, 7, 29, 15, 22), 5)
# Since the minute window is 5, 15:22 rounds to 15:25
# Output | 2024-07-29 15:25:00

round_timestamp_up(dt.datetime(2024, 7, 29, 15, 22), 1)
# Since the minute window is only 1, 15:22 only rounds to 15:22
# Output | 2024-07-29 15:22:00

# sample_frame:
#    id                    BinTime
# 0   1  2024-07-29 09:04:00+00:00
# 1   2  2024-07-29 08:59:00+00:00
# 2   3        2024-07-29 08:41:00

sample_frame["EndTime"] = sample_frame.BinTime.apply(lambda x: tu.round_timestamp_up(x, 5))

# Output frame:
#    id                    BinTime                    EndTime
# 0   1  2024-07-29 09:04:00+00:00  2024-07-29 09:05:00+00:00
# 1   2  2024-07-29 08:59:00+00:00  2024-07-29 09:00:00+00:00
# 2   3        2024-07-29 08:41:00        2024-07-29 08:45:00
```

`minutes_offset`

Calculates the number of minutes until the next N-minute block of the hour. For use with the `round_timestamp_up` function. N must be a divisor of 60 minutes, and the time must have 0 seconds, milliseconds, etc.

Examples:

```python
from core_utils.time_utils import minutes_offset

minutes_offset(pd.Timestamp(2024, 7, 29, 15, 22), 5)
# The next 5-minute interval is 3 minutes later (15:25)
# Output | 3

minutes_offset(dt.datetime(2024, 7, 29, 15, 22), 1)
# The next 1-minute interval is 0 minutes later (15:22)
# Output | 0
```

## Working with Timezones

An important part of dealing with datetimes is to make use of Timezones. This documentation page covers how to work with timezones when using the functions of `core_utils.time_utils`.

**NOTE:** the timezone-aware functions in time_utils assume that timezones used come directly from time_utils.py, and will likely not work with manually created timezones. You can work with built-in timezones in one of two ways:

- time_utils.py contains two global "built-in" timezones, `nyc_timezone` and `utc_timezone`.
- Most of the functions in time_utils.py accept a `zone` parameter. You can pass strings to this field - use "ET" or "NYC" for US Eastern Time, or "GMT" or "UTC" for Greenwich Mean Time.

### Timezone libraries

If you are using timezoned datetimes in Python with `time_utils`, you must have the required library installed based on your current Python version (see below). If you try to supply a timezone to a time_utils function without the proper library installed, the library will throw a `TimezoneLibMissingError`.

time_utils uses the built-in [`zoneinfo`](https://docs.python.org/3/library/zoneinfo.html) library to manage Timezones.

### Basic Usage

To use timezones, simply pass a `zone` to any of the time_utils functions:

```python
from core_utils.time_utils import datetime_from_date_and_time, datetime_from_time_and_date_start_time, now_nyc
from datetime import datetime

some_ny_datetime = datetime_from_date_and_time(datetime.today(), "18:00", zone="NYC")
some_utc_datetime = datetime_from_time_and_date_start_time("09:00", "22:00", now=now_nyc(), zone="UTC")
```


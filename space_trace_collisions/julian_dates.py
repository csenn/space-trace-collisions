from typing import Tuple
from sgp4.api import days2mdhms # type: ignore
from datetime import datetime, timedelta, timezone

JulianDate = Tuple[float, float]


# def jd_to_python_date(julian_date: JulianDate) -> datetime:
#     month, day, hour, minute, second = days2mdhms(julian_date[0], julian_date[1])

#     return datetime(year, month, day, hour, minute, second)


def julian_date_to_datetime(julian_date: JulianDate) -> datetime:
    jd, fraction_of_day = julian_date
    # Julian Date to Gregorian conversion
    # Reference: Julian Date 2451545.0 is 2000-01-01 12:00:00 UTC
    
    jd -= 0 # 0.5  # Adjust for the start of the day
    days_since_epoch = jd - 2451545.0
    epoch = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)  # 2000-01-01 12:00:00 UTC
    date = epoch + timedelta(days=days_since_epoch + fraction_of_day)
    
    return date


def jd_to_float(julian_date: JulianDate) -> float:
    """Combine jd and fr into one float."""
    return julian_date[0] + julian_date[1]

def float_to_jd(value: float) -> JulianDate:
    """Split a float julian day back into (jd, fr)."""
    from math import floor
    jd_int = floor(value)
    fr = value - jd_int
    return jd_int, fr


def add_time(time: JulianDate, seconds: float) -> JulianDate:
    """
    time: (jd, fr)
    seconds: number of seconds to add
    returns: (jd, fr) with seconds added
    """
    # Convert (jd, fr) -> single float
    combined = jd_to_float(time)

    # Convert seconds to days
    delta_days = seconds / 86400.0

    # Add
    new_combined = combined + delta_days

    # Convert back (split out) for SGP4
    return float_to_jd(new_combined)


def difference_in_time_in_seconds(time_1: JulianDate, 
                                  time_2: JulianDate) -> float:
    """
    Returns time_1 - time_2 in seconds (time_1 is later? => positive).
    """
    combined_1 = jd_to_float(time_1)
    combined_2 = jd_to_float(time_2)
    diff_days = (combined_1 - combined_2)  # could be negative if time_1 < time_2
    diff_seconds = diff_days * 86400.0
    return diff_seconds

def get_midpoint_time(time_1: JulianDate, 
                      time_2: JulianDate) -> JulianDate:
    """
    Returns the midpoint in Julian days of two times.
    """
    combined_1 = jd_to_float(time_1)
    combined_2 = jd_to_float(time_2)
    midpoint = (combined_1 + combined_2) / 2.0
    return float_to_jd(midpoint)


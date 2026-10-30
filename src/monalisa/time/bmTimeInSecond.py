"""Port of src/time/bmTimeInSecond.m."""

import datetime as dt


def bmTimeInSecond():
    """Seconds elapsed since the start of the current month (MATLAB definition)."""
    d = dt.datetime.now()
    return d.second + d.microsecond * 1e-6 + d.minute * 60 + d.hour * 60**2 + d.day * 24 * 60**2

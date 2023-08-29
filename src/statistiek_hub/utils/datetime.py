"""Utilities set for data processing"""
from datetime import datetime

from dateutil.relativedelta import *


def convert_to_datetime(date: str = None, format: str = "%Y%m%d"):
    """Convert string format to datetime"""
    if date in [None, " ", ""]:
        return ""

    date = date.replace("-", "")

    try:
        date = datetime.strptime(date, format)
    except ValueError:
        try:
            year = int(date[0:4])
            month = int(date[4:6])
            day = int(date[6:8])
            date = datetime(
                year, month if month != 0 else month + 1, day if day != 0 else day + 1
            )
        except ValueError:
            return f"verkeerd format: {date}"

    return date


def add_timedelta(date, delta: str = None):
    """Add timedelta to datetime"""

    delta_date = None
    delta = str(delta)
    if delta == "Dag":
        delta_date = date + relativedelta(days=+1)
    elif delta == "Week":
        delta_date = date + relativedelta(weeks=+1)
    elif delta == "Maand":
        delta_date = date + relativedelta(months=+1)
    elif delta == "Kwartaal":
        delta_date = date + relativedelta(months=+3)
    elif delta == "Jaar":
        delta_date = date + relativedelta(years=+1)
    elif delta == "Peildatum":
        delta_date = date

    return delta_date


def convert_to_date(date: str = None, format: str = "%Y%m%d") -> datetime.date:
    """Convert string format to date"""

    _date = convert_to_datetime(date, format)

    if type(_date) != str:
        _date = _date.date()
    else:
        _date = _date

    return _date

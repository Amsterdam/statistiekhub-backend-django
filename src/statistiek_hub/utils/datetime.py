"""Utilities set for data processing"""
from datetime import datetime

from dateutil.relativedelta import *


def convert_to_datetime(date: str = None) -> datetime:
    """Convert string format %Y%m%d (/,-) to datetime with time as 0 or %d/%m/%y %H:%M of %Y-%m-%d %H:%M:%S.%f to datetime"""

    if date in [None, " ", ""]:
        return ""

    formats_allowed = [
        "%Y%m%d",
        "%Y/%m/%d",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S.%f",
        "%d/%m/%y %H:%M",
    ]

    _date = None

    for format in formats_allowed:
        try:
            _date = datetime.strptime(date, format)
            break
        except ValueError:
            pass

    if _date == None:
        # probeer O&S aanlever-format

        # remove date notation
        replace_list = ["-", "/"]
        for i in replace_list:
            date = date.replace(i, "")

        try:
            year = int(date[0:4])
            month = int(date[4:6])
            day = int(date[6:8])
            _date = datetime(
                year,
                month if month != 0 else month + 1,
                day if day != 0 else day + 1,
            )
        except:
            raise ValueError(
                f"verkeerd datumformat voor {date}, toegestane formats zijn {formats_allowed}"
            )

    return _date


def add_timedelta(date: datetime, delta: str = None):
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


def convert_to_date(date: str = None) -> datetime.date:
    """Convert string format to date"""

    _date = convert_to_datetime(date)

    if type(_date) != str:
        _date = _date.date()
    else:
        _date = _date

    return _date

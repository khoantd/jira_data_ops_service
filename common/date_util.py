# import datetime
from datetime import datetime


def lom(year, month, day):
    d = datetime.date(year + int(month/12), month %
                      12+1, 1)-datetime.timedelta(days=1)  # type: ignore
    return d


def daysdiff_between_dates(date1: datetime, date2: datetime):
    return (date1-date2).days

# print(lom(2021, 5, 16))

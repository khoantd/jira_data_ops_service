import configparser
from business_calendar import Calendar, MO, TU, WE, TH, FR
import datetime

BIZ_CAL = Calendar(workdays=[MO, TU, WE, TH, FR])


def biz_days_calculate(input_date, days):
    date1 = input_date
    date2 = BIZ_CAL.addbusdays(date1, days)
    return {
        "input_date": input_date.strftime("%d-%m-%Y"),
        "isowrkingday": BIZ_CAL.isworkday(input_date),
        "days": BIZ_CAL.busdaycount(date1, date2),
        "suggested_start_date": BIZ_CAL.adjust(date1, 1).strftime("%d-%m-%Y"),
        "suggested_end_date": date2.strftime("%d-%m-%Y")
    }


def biz_days_btwn_days_calculate(input_date_1, input_date_2):
    days = BIZ_CAL.busdaycount(input_date_1, input_date_2)
    return days


def biz_days_check(input_date):
    if BIZ_CAL.isworkday(input_date) != True:
        return {
            "input_date": input_date.strftime("%d-%m-%Y"),
            "isowrkingday": BIZ_CAL.isworkday(input_date),
            "suggested_start_date": BIZ_CAL.adjust(input_date, 1).strftime("%d-%m-%Y"),
        }
    else:
        return {
            "input_date": input_date.strftime("%d-%m-%Y"),
            "isowrkingday": BIZ_CAL.isworkday(input_date),
        }


def cfg_read(section, parameter):
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    config.sections()
    return config[f'{section}'][f'{parameter}']


if __name__ == "__main__":
    print("util.py")

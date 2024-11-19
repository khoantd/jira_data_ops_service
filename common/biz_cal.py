from business_calendar import Calendar, MO, TU, WE, TH, FR
import datetime

# normal calendar, no holidays
# cal = Calendar()
# date2 = cal.addbusdays(date1, 25)
# print('%s days between %s and %s' %
#       (cal.busdaycount(date1, date2), date1, date2))

# don't work on Fridays? no problem!
BIZ_CAL = Calendar(workdays=[MO, TU, WE, TH, FR])


def biz_days_calculate(input_date, days):
    date1 = input_date
    date2 = BIZ_CAL.addbusdays(date1, days)
    return {
        "input_date": input_date.strftime("%Y-%m-%d"),
        "isowrkingday": BIZ_CAL.isworkday(input_date),
        "days": BIZ_CAL.busdaycount(date1, date2),
        "suggested_start_date": BIZ_CAL.adjust(date1, 1).strftime("%Y-%m-%d"),
        "suggested_end_date": date2.strftime("%Y-%m-%d"),
    }
    # print('%s days between %s and %s' %
    #       (BIZ_CAL.busdaycount(date1, date2), date1, date2))

# Count number of business days between 2 dates


def biz_days_count(date1, date2):
    return {"no_of_biz_days": BIZ_CAL.busdaycount(date1, date2)}


def estimation_review(date1, date2, estimation):
    biz_days = float(biz_days_count(date1, date2)["no_of_biz_days"])
    # result = biz_days/estimation
    print("estimation:", estimation)
    print("biz_days:", biz_days)
    result = "0"
    remarks = ""
    if biz_days > 0:
        result = estimation/biz_days
        if result > 1:
            remarks = f"Over estimation"
        elif result == 1:
            remarks = "Fine estimation"
        else:
            remarks = f"Under estimation"
    else:
        remarks = f"Under estimation"

    return {"remarks": remarks,
            "diff": round((float(result)-1), 2)}


def completion_review(date1, date2):
    biz_days = float(biz_days_count(date1, date2)["no_of_biz_days"])
    # print(biz_days)
    remarks = ""
    if biz_days > 0:
        remarks = f"Missed defined deadline"
    elif biz_days == 0:
        remarks = "Finished on time"
    else:
        remarks = f"Finished before the defined deadline"
    return {"remarks": remarks,
            "diff": biz_days}


def week_number_of_month(date_value):
    return (date_value.isocalendar()[1] - date_value.replace(day=1).isocalendar()[1] + 1)


# holiday? no problem!
# cal = Calendar(workdays=[MO, TU, WE, TH], holidays=['2013-01-17'])
# date2 = cal.addbusdays(date1, 25)
# print('%s days between %s and %s' %
#       (cal.busdaycount(date1, date2), date1, date2))
if __name__ == "__main__":
    local = datetime.datetime.now()
    date2 = BIZ_CAL.addbusdays(local, 5)
    date3 = BIZ_CAL.addbusdays(local, -3)
    print(local.isocalendar()[1])
    print("month ", local.strftime("%m"),
          " and week", week_number_of_month(local))
    print(biz_days_calculate(local, 25))
    print(biz_days_count(local, date2))
    print(estimation_review(local, date3, 6))
    print(completion_review(local, date3))

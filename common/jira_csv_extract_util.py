import json
import csv
from common.json_util import read_json_file, parse_json, parse_json_v2
from atlassian import Jira
from datetime import datetime
import os

from common.status_cr import biz_and_jira_mapped_status, status_details_and_jira_mapped_status


jira = Jira(
    url='https://fecredit.atlassian.net',
    username='khoa.nguyen.24@fecredit.com.vn',
    password='AEqPCgn5b5BSOArR0Aqu612D')  # password is a generated Token


def jira_csv_extract(file_name, JQL, systemname):
    header = ['system_name', 'key', 'summary', 'change request type', 'created', 'month', 'created_in_dec_2021', 'created_in_jan_2022', 'created_in_feb_2022', 'year',
              'age_till_dec_2021', 'late_cr_in_dec_2021_flag', 'age_till_jan', 'late_cr_in_jan_flag', 'age_till_feb', 'late_cr_in_feb_flag', 'age_till_now', 'updated_date', 'days_since_updated', 'status', 'biz_status', 'it_status']
    issues = jira.jql_get_list_of_tickets(JQL)
    json_object = json.dumps(issues, indent=4)
    json_data = json.loads(json_object)
    parsing_paths_data = read_json_file("data/input/parsing_paths_v1.json")
    # list = []
    try:
        if check_csv_empty(file_name) == True:
            csv_initiate(file_name, header, json_data,
                         parsing_paths_data, systemname)
        else:
            csv_append(file_name, json_data, parsing_paths_data, systemname)
    except FileNotFoundError:
        csv_initiate(file_name, header, json_data,
                     parsing_paths_data, systemname)


def csv_append(file_name, json_data, data, systemname):
    print("Start processing ", systemname)
    with open(file_name, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for json_item in json_data:
            age = 0
            current_date = datetime.now()
            dec_2021 = '2021-12-31T00:00:00.000'
            jan = '2022-01-31T00:00:00.000'
            feb = '2022-02-28T00:00:00.000'
            date_obj_dec_21 = datetime. strptime(
                dec_2021, '%Y-%m-%dT%H:%M:%S.%f')
            date_obj_jan = datetime. strptime(
                jan, '%Y-%m-%dT%H:%M:%S.%f')
            date_obj_feb = datetime. strptime(
                feb, '%Y-%m-%dT%H:%M:%S.%f')
            row = []
            row.append(systemname)
            for item in data:
                # obj = parse_json(data[item], json_item)
                obj = parse_json_v2(data[item], json_item)
                row.append(obj)
                if item == "created":
                    created_date_time_obj = datetime.strptime(
                        obj.rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')
                    created_date_time_obj = datetime.strptime(
                        obj.rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')
                    age = (current_date-created_date_time_obj).days
                    row.append(int(created_date_time_obj.strftime('%m')))
                    if int(created_date_time_obj.strftime('%m')) == 12:
                        row.append(1)
                    else:
                        row.append(0)
                    if int(created_date_time_obj.strftime('%m')) == 1:
                        row.append(1)
                    else:
                        row.append(0)
                    if int(created_date_time_obj.strftime('%m')) == 2:
                        row.append(1)
                    else:
                        row.append(0)
                    row.append(int(created_date_time_obj.strftime('%Y')))
                    row.append(
                        int((date_obj_dec_21-created_date_time_obj).days))
                    if int((date_obj_dec_21-created_date_time_obj).days) >= 90:
                        row.append(1)
                    else:
                        row.append(0)
                    row.append(int((date_obj_jan-created_date_time_obj).days))
                    if int((date_obj_jan-created_date_time_obj).days) >= 90:
                        row.append(1)
                    else:
                        row.append(0)
                    row.append(int((date_obj_feb-created_date_time_obj).days))
                    if int((date_obj_feb-created_date_time_obj).days) >= 90:
                        row.append(1)
                    else:
                        row.append(0)
                    row.append(age)
                if item == "updated":
                    updated_date_time_obj = datetime.strptime(
                        obj.rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')
                    daysofupdate = (
                        current_date-updated_date_time_obj).days
                    row.append(daysofupdate)
                if item == "status":
                    row.append(biz_and_jira_mapped_status(obj))
                    row.append(status_details_and_jira_mapped_status(obj))
            writer.writerow(row)
    print(systemname, " is accomplished")


def csv_initiate(file_name, header, json_data, data, systemname):
    print("Start processing ", systemname)
    with open(file_name, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # write the header
        writer.writerow(header)
        for json_item in json_data:
            age = 0
            current_date = datetime.now()
            dec_2021 = '2021-12-31T00:00:00.000'
            jan = '2022-01-31T00:00:00.000'
            feb = '2022-02-28T00:00:00.000'
            date_obj_dec_21 = datetime. strptime(
                dec_2021, '%Y-%m-%dT%H:%M:%S.%f')
            date_obj_jan = datetime. strptime(
                jan, '%Y-%m-%dT%H:%M:%S.%f')
            date_obj_feb = datetime. strptime(
                feb, '%Y-%m-%dT%H:%M:%S.%f')
            row = []
            row.append(systemname)
            for item in data:
                # obj = parse_json(data[item], json_item)
                obj = parse_json_v2(data[item], json_item)
                row.append(obj)
                if item == "created":
                    created_date_time_obj = datetime.strptime(
                        obj.rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')
                    created_date_time_obj = datetime.strptime(
                        obj.rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')
                    age = (current_date-created_date_time_obj).days
                    row.append(int(created_date_time_obj.strftime('%m')))
                    if int(created_date_time_obj.strftime('%m')) == 12:
                        row.append(1)
                    else:
                        row.append(0)
                    if int(created_date_time_obj.strftime('%m')) == 1:
                        row.append(1)
                    else:
                        row.append(0)
                    if int(created_date_time_obj.strftime('%m')) == 2:
                        row.append(1)
                    else:
                        row.append(0)
                    row.append(int(created_date_time_obj.strftime('%Y')))
                    row.append(
                        int((date_obj_dec_21-created_date_time_obj).days))
                    if int((date_obj_dec_21-created_date_time_obj).days) >= 90:
                        row.append(1)
                    else:
                        row.append(0)
                    row.append(int((date_obj_jan-created_date_time_obj).days))
                    if int((date_obj_jan-created_date_time_obj).days) >= 90:
                        row.append(1)
                    else:
                        row.append(0)
                    row.append(int((date_obj_feb-created_date_time_obj).days))
                    if int((date_obj_feb-created_date_time_obj).days) >= 90:
                        row.append(1)
                    else:
                        row.append(0)
                    row.append(age)
                if item == "updated":
                    updated_date_time_obj = datetime.strptime(
                        obj.rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')
                    daysofupdate = (
                        current_date-updated_date_time_obj).days
                    row.append(daysofupdate)
                if item == "status":
                    row.append(biz_and_jira_mapped_status(obj))
                    row.append(status_details_and_jira_mapped_status(obj))
            writer.writerow(row)
    print(systemname, " is accomplished")
    # return list


def check_csv_empty(filename):
    if os.stat(filename).st_size == 0:
        return True
    else:
        return False


if __name__ == "__main__":
    print(check_csv_empty("data/output/Vtiger.csv"))

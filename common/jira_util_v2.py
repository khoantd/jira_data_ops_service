from asyncore import read
from datetime import datetime

from .json_util import parse_json_v2, read_json_file
# from types import NoneType
# from atlassian import Jira
import datetime
import csv
# from age_of_status_cal import perform_operation
# from s3_aws_cli_push import download_file_from_s3
# from common.jira_csv_extract_util_v2 import check_csv_empty

from common.status_cr import it_status_and_operation


def find_current_state_issue(key, it_status, filename):
    try:
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # check the arguments against the row
                if (row['key'] == key and
                        row['it_status'] == it_status):
                    return dict(row)
    except FileNotFoundError:
        print(f"The file ", filename, " does not exist")


def age_of_phase_increment(phase, updated_date_str, row):
    today = datetime.now()
    updated_date = datetime.strptime(
        updated_date_str.rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')
    print((today-updated_date).days)
    headers = ['initiation', 'analysis',
               'in_queue_dev', 'in_dev', 'uat', 'hold', 'done', 'can_reject']
    for item in headers:
        if phase == item:
            print(row)
            row[item] = (today-updated_date).days
    return row


def json_to_row_data_convert(pasring_path_file, data):
    parsing_path_data = read_json_file(pasring_path_file)
    for rec in data:
        row = []
        for json_path_item in parsing_path_data:
            row.append(parse_json_v2(parsing_path_data[json_path_item], rec))
    return row

# Extract date of a specific stage from histories
# input: JSON array of histories and a specific stage
# output: date ("%Y-%m-%d")


def date_of_stage_get(histories, current_stage):
    created_date = None
    created_date = date_of_changed_value_of_field_get(
        histories, 'status', current_stage)
    if created_date != None:
        created_date = created_date.strftime("%Y-%m-%d")
    return created_date


def transitions_details_get(histories, current_stage):
    transitions = []
    transitions = dtl_date_of_changed_value_of_field_get(
        histories, 'status', current_stage)
    return transitions

# Extract date of value changed of a specific field from histories
# input: JSON array of histories and field name and a specific value
# output: date ("%Y-%m-%d")


def date_of_changed_value_of_field_get(histories, field_name, current_stage):
    created_date = None
    for i in range(len(histories)):
        items = parse_json_v2("$.items", histories[i])
        for item in items:
            field = parse_json_v2("$.field", item)
            if field == field_name:
                status = parse_json_v2("$.toString", item)
                # print("status:", status)
                if status in current_stage:
                    created_date = datetime.datetime.strptime(
                        parse_json_v2("$.created", histories[i]).rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')

    return created_date


def dtl_date_of_changed_value_of_field_get(histories, field_name, current_stage):
    created_date = None
    transitions = []
    for i in range(len(histories)):
        items = parse_json_v2("$.items", histories[i])
        for item in items:
            field = parse_json_v2("$.field", item)
            counter = 0
            transition = None
            if field == field_name:
                to_status = parse_json_v2("$.toString", item)
                # print("status:", status)
                if to_status in current_stage:
                    from_status = parse_json_v2("$.fromString", item)
                    created_date = datetime.datetime.strptime(
                        parse_json_v2("$.created", histories[i]).rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')
                    transition = {
                        "from_status": from_status,
                        "to_status": to_status,
                        "date": created_date.strftime("%Y-%m-%d")
                    }
                    transitions.append(transition)
                    counter = counter+1
    return transitions

# def cr_age_calculate(source_filename, target_filename):
#     # if check_csv_empty("../data/output/CRs_of_Systems_short.csv") == True:
#     if check_csv_empty(source_filename) == True:
#         print(f"The file ", source_filename,
#               " does not exist")
#     else:
#         # op = open("../data/output/CRs_of_Systems_short.csv", "r")
#         op = open(source_filename, "r")
#         dt = csv.DictReader(op)
#         print(dt)
#         up_dt = []
#         phase_name = ""
#         read_row = {}
#         t_cnt = 0
#         for r in dt:
#             t_cnt = t_cnt+1
#             read_row = find_current_state_issue(
#                 r['key'], r['it_status'], target_filename)
#             if read_row != None:
#                 # today = datetime.now().strftime("%m/%d/%Y")
#                 # updated_date_str = read_row['updated_date']
#                 # updated_date = datetime.strptime(
#                 #     updated_date_str, "%m/%d/%Y").strftime("%m/%d/%Y")
#                 # if today != updated_date:
#                 phase_name = it_status_and_operation(r['it_status'])
#                 read_row = age_of_phase_increment(
#                     phase_name, r['updated_date'], read_row)
#                 # else:
#                 print("The data is up to date!")
#             else:
#                 read_row = {
#                     'system_name': r['system_name'],
#                     'key': r['key'],
#                     'it_status': r['it_status'],
#                     'created_date': datetime.now().strftime("%m/%d/%Y"),
#                     'updated_date': datetime.now().strftime("%m/%d/%Y"),
#                     'initiation': 0,
#                     'analysis': 0,
#                     'in_queue_dev': 0,
#                     'in_dev': 0,
#                     'uat': 0,
#                     'hold': 0,
#                     'done': 0,
#                     'can_reject': 0
#                 }
#             up_dt.append(read_row)
#         op.close()
#         # op = open("../data/output/CRs_of_Systems_status_age.csv",
#         #           "w", newline='')
#         op = open(target_filename,
#                   "w", newline='')
#         headers = ['system_name', 'key', 'it_status', 'created_date', 'updated_date', 'initiation',
#                    'analysis', 'in_queue_dev', 'in_dev', 'uat', 'hold', 'done', 'can_reject']
#         data = csv.DictWriter(op, delimiter=',', fieldnames=headers)
#         data.writerow(dict((heads, heads) for heads in headers))
#         data.writerows(up_dt)

#         op.close()


if __name__ == "__main__":
    s3_bucket = "sg-static-website"
    name = "CRs_of_Systems.csv"
    source_filename = "../data/output/CRs_of_Systems.csv"
    target_filename = "../data/output/CRs_of_Systems_age.csv"
    # download_file_from_s3(name, source_filename, s3_bucket)
    cr_age_calculate(source_filename, target_filename)

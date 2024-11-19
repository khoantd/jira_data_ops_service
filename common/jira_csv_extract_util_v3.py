import json
import csv
from common.json_util import read_json_file, parse_json, parse_json_v2
from atlassian import Jira
from datetime import datetime
import os
from common.status_cr import biz_and_jira_mapped_status, status_details_and_jira_mapped_status
from common.it_project_mapping import project_categorize
from common.project_type_mapping import project_type_categorize


jira = Jira(
    url='https://fecredit.atlassian.net',
    username='khoa.nguyen.24@fecredit.com.vn',
    password='AEqPCgn5b5BSOArR0Aqu612D')  # password is a generated Token


def jira_csv_extract_v2(operation_name, headers, file_name_output, input_data, parsing_path):
    print(operation_name)
    if operation_name == "":
        csv_initiate(file_name_output, headers, input_data, parsing_path)
    # jira_projects_extract(file_name, JQL, systemname)


def csv_initiate(file_name_output, headers, input_data, parsing_path):
    print("Start processing ", file_name_output)
    with open(file_name_output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # write the headers
        writer.writerow(headers)
        # wrtie the records
        jira_issue_data_write_v2(parsing_path, input_data, writer)


def jira_issue_data_write_v2(parsing_path, data, writer):
    parsing_path_data = read_json_file(parsing_path)
    print(parsing_path_data)
    counter = 0
    for rec in data:
        row = []
        division = ""
        for json_path_item in parsing_path_data:
            row.append(parse_json_v2(parsing_path_data[json_path_item], rec))
        division = project_categorize(row[1])
        print(str(row[4]))
        print(project_type_categorize(str(row[4])))
        project_type = project_type_categorize(str(row[4]))
        row.append(division)
        row.append(project_type)
        print("Division name: ", division)
        writer.writerow(row)
        counter = counter+1
    print("Total records: ", counter)


def check_csv_empty(filename):
    if os.stat(filename).st_size == 0:
        return True
    else:
        return False


if __name__ == "__main__":
    print(check_csv_empty("data/output/Vtiger.csv"))

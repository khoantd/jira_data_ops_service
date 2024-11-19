import json
import csv

from common.date_util import daysdiff_between_dates

from common.csv_util import check_csv_empty

from common.json_util import json_key_get

from common.jira_util_v2 import *
from common.json_util import read_json_file, parse_json, parse_json_v2
from atlassian import Jira
from datetime import datetime
# import os

from common.status_cr import biz_and_jira_mapped_status, filtered_statuses_list_get, status_details_and_jira_mapped_status
from common.issue_field_handler_v2 import perform_operation
from services.ruleengine_exec import rules_exec

jira = Jira(
    url='https://fecredit.atlassian.net',
    username='khoa.nguyen.24@fecredit.com.vn',
    password='AEqPCgn5b5BSOArR0Aqu612D')  # password is a generated Token


def late_cr_v6_extract(file_name, JQL, systemname, parsing_file_path, p_status, p_fields):
    headers = ['system_name', 'key', 'current_status',
               'from_status', 'from_it_status', 'to_status', 'to_it_status', 'date_of_change', 'age_since_approval', 'age_since_deploy_date', 'reporter', 'accountid', 'need_to_remind_yn']
    # fields = ['key', 'status', 'changelog', 'created']
    # print(p_fields)
    issues = jira.jql_get_list_of_tickets(
        JQL, fields=p_fields, expand='changelog')
    print("JQL:", JQL)
    print("Count: ", len(issues))
    json_object = json.dumps(issues, indent=4)
    json_data = json.loads(json_object)
    parsing_paths_data = read_json_file(parsing_file_path)
    # list = []
    try:
        # print("file_name:", file_name)
        file_is_empty = check_csv_empty(file_name)
        # print("file_is_empty: ", file_is_empty)
        if file_is_empty:
            # print("File does not exist")
            csv_v5_initiate(file_name, headers, json_data,
                            parsing_paths_data, systemname, p_status)
        else:
            # print("check_csv_empty(file_name)", check_csv_empty(file_name))
            # print("File exists")
            csv_v5_append(file_name, json_data,
                          parsing_paths_data, systemname, p_status)
    except FileNotFoundError:
        csv_v5_initiate(file_name, headers, json_data,
                        parsing_paths_data, systemname, p_status)


def csv_v5_initiate(file_name, header, json_data, data, systemname, p_status):
    it_stage = []
    if p_status == 'completed':
        it_stage = ['5. Done', '6. Cancel or Rejected']
    if p_status == 'postapproval':
        it_stage = ['9. In progress of Deployment',
                    '10. Deployed', '5. Approved']
    if p_status == 'inreview':
        it_stage = ['1. In Review']
    print(it_stage)
    with open(file_name, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        counter = data_rows_prepare(
            json_data, data, systemname, it_stage, writer)

    print(systemname, " is accomplished counter=", counter)


def data_rows_prepare(json_data, data, systemname, it_stage, writer):
    counter = 0
    for json_item in json_data:
        # print("json_item:", json_item)
        # row = []
        transtions = []
        # created_date = None
        rows = []
        key = None
        status = None
        current_date = datetime.now()
        reporter = None
        accountId = None
        expectedDate = None
        days_since_approval = None
        days_since_expected_date = None
        # row.append(systemname)
        # age = 0
        # status = ""
        # approval_status = ""
        # print("data", data)
        for item in data:
            # print('item', item)
            # key = None
            l_obj = perform_operation(item, json_item, data[item])
            # print('item: ', item)
            # print('l_obj: ', l_obj)
            # print('item: ', item)
            # row = csv_data_row_v3_add(row, item, l_obj)
            if item == 'key':
                key = l_obj
                # print('key', key)
            if item == 'status':
                status = l_obj
            if item == 'requestor':
                reporter = l_obj
            if item == 'accountId':
                accountId = l_obj
                # if l_obj != 'Not Available':
            if item == 'expectedDate':
                expectedDate = l_obj

                # print('expectedDate', expectedDate)
            transtions = dtl_transitions_gen(item, l_obj, it_stage)
            # transtions.sort(key=takeFourth)
            # if item == 'created':
            #     created_date = datetime.strptime(l_obj.rsplit(
            #         "+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f').strftime("%Y-%m-%d")
            for transition_arr in transtions:
                # print("len(transition_arr),", len(transition_arr))
                if len(transition_arr) > 0:
                    # transition_arr.sort(key=takeFourth)
                    # row = []
                    for item in transition_arr:
                        # print(item)
                        row = []
                        row.append(systemname)
                        row.append(key)
                        row.append(status)
                        row.append(item.get("from_status"))
                        row.append(status_details_and_jira_mapped_status(
                            item.get("from_status")))
                        row.append(item.get("to_status"))
                        row.append(status_details_and_jira_mapped_status(
                            item.get("to_status")))
                        row.append(item.get("date"))
                        days_since_start_review = daysdiff_between_dates(
                            current_date, datetime.strptime(
                                item.get("date"), '%Y-%m-%d'))
                        row.append(days_since_start_review)
                        days_since_expected_date = daysdiff_between_dates(
                            current_date, datetime.strptime(expectedDate, '%Y-%m-%d'))  # type: ignore
                        row.append(days_since_expected_date)
                        row.append(reporter)
                        row.append(accountId)
                        row.append(supplement_info_reminder_check(
                            days_since_start_review))
                        # print("row,", row)
                        rows.append(row)
                        # rows.append(row)
        rows.sort(key=takeFourth)
        for item in rows:
            # print("item:", item)
            writer.writerow(item)
            counter += 1
    return counter


def closing_ticket_reminder_check(p_days_since_approval, p_days_since_expected_date, p_threshold):
    if p_threshold == 0:
        p_threshold = 1
    result_of_modulus = p_days_since_expected_date % p_threshold
    data = {
        'p_days_since_approval': p_days_since_approval,
        'p_days_since_expected_date': p_days_since_expected_date,
        'result_of_modulus': result_of_modulus
    }
    result = rules_exec(data)
    if result['action_recommendation'] == 'send_reminder_to_close_ticket':
        # print(result['action_recommendation'])
        # print(result['pattern_result'])
        return result['pattern_result'].replace("-", "")
    else:
        # print(result['action_recommendation'])
        # print(result['pattern_result'])
        return 'N'


def supplement_info_reminder_check(p_days_since_start_review, p_threshold=2):
    if p_threshold == 0:
        p_threshold = 1
    result_of_modulus = p_days_since_start_review % p_threshold
    print("p_days_since_start_review:", p_days_since_start_review)
    data = {
        'p_days_since_start_review': p_days_since_start_review,
        'result_of_modulus': result_of_modulus
    }
    result = rules_exec(data)
    print(result)
    # if result['action_recommendation'] == 'send_reminder_to_ask_information':
    #     print(result['action_recommendation'])
    #     # print(result['pattern_result'])
    #     return result['pattern_result'].replace("-Y-", "Y")
    # elif result['action_recommendation'] == 'change_to_rejected_status':
    #     print(result['action_recommendation'])
    #     # print(result['pattern_result'])
    #     return result['pattern_result'].replace("-YY", "Y")
    # else:
    #     print(result['action_recommendation'])
    #     # print(result['pattern_result'])
    #     return 'N'
    return result['action_recommendation']


def reminder_send_check(p_days_since_approval, p_days_since_expected_date, p_threshold):
    # Assign 1 to p_threshold if p_threshold has zero input
    if p_threshold == 0:
        p_threshold = 1
    result_of_modulus = p_days_since_expected_date % p_threshold
    data = {
        'p_days_since_approval': p_days_since_approval,
        'p_days_since_expected_date': p_days_since_expected_date,
        'result_of_modulus': result_of_modulus
    }
    result = rules_exec(data)
    if result['action_recommendation'] == 'send_reminder_to_close_ticket':
        # print(result['action_recommendation'])
        # print(result['pattern_result'])
        return result['pattern_result']
    else:
        # print(result['action_recommendation'])
        # print(result['pattern_result'])
        return 'N'
    # calc = daysdiff_between_dates(
    #     p_current_date, datetime.strptime(
    #         p_expectedDate, '%Y-%m-%d'))
    # threshold = p_threshold
    # if p_days_since_approval > 0 and p_days_since_expected_date > 0:
        # if p_days_since_expected_date % p_threshold == 0:
        # print("p_days_since_approval",p_days_since_approval)
        # print("p_days_since_expected_date",p_days_since_expected_date)
        # print("p_threshold",p_threshold)
        # return 'Y'
    # else:
    #     return 'N'


def dtl_record_analysis_gen(row, item, l_obj):
    if l_obj != 'Not Available':
        if item == 'histories':
            row.append(date_of_stage_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), it_stage)))
            row.append(date_of_stage_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), it_stage)))
            row.append(date_of_stage_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), it_stage)))
            row.append(date_of_stage_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), it_stage)))
            row.append(date_of_stage_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), it_stage)))
        elif item == 'created':
            row.append(datetime.strptime(
                l_obj.rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f').strftime("%Y-%m-%d"))
        elif item == "status":
            row.append(l_obj)
            row.append(biz_and_jira_mapped_status(l_obj))
            row.append(status_details_and_jira_mapped_status(l_obj))
        else:
            row.append(l_obj)


def dtl_transitions_gen(item, l_obj, it_stage=[]):
    # print("it_stage", it_stage)
    transtitions = []
    if item == 'histories':
        if '0. New/Open' in it_stage:
            transtitions.append(transition_dtl_extract(transitions_details_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), '0. New/Open'))))
        elif '1. In Review' in it_stage:
            transtitions.append(transition_dtl_extract(transitions_details_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), '1. In Review'))))
        elif '2. In Security Review' in it_stage:
            transtitions.append(transition_dtl_extract(transitions_details_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), '2. In Security Review'))))
        elif '3. Waiting for Approval' in it_stage:
            transtitions.append(transition_dtl_extract(transitions_details_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), '3. Waiting for Approval'))))
        elif '4. Waiting for CAB Approval' in it_stage:
            transtitions.append(transition_dtl_extract(transitions_details_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), '4. Waiting for CAB Approval'))))
        elif '5. Approved' in it_stage:
            transtitions.append(transition_dtl_extract(transitions_details_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), '5. Approved'))))
        elif '9. In progress of Deployment' in it_stage:
            transtitions.append(transition_dtl_extract(transitions_details_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), '9. In progress of Deployment'))))
        elif '10. Deployed' in it_stage:
            transtitions.append(transition_dtl_extract(transitions_details_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), '10. Deployed'))))
        elif '6. Done' in it_stage:
            transtitions.append(transition_dtl_extract(transitions_details_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), '6. Done'))))
        elif '7. Canceled' in it_stage:
            transtitions.append(transition_dtl_extract(transitions_details_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), '7. Canceled'))))
        elif '8. Rejected' in it_stage:
            transtitions.append(transition_dtl_extract(transitions_details_get(l_obj, json_key_get(
                read_json_file(
                    "config-pattern/jira_cr_statuses_obj.json"), '8. Rejected'))))
        else:
            pass
        # print("transtitions:", transtitions)
    return transtitions


def transition_dtl_extract(p_transtion_ls):
    transition = []
    if isinstance(p_transtion_ls, list):
        if len(p_transtion_ls) > 0:
            for item in p_transtion_ls:
                transition.append(item)
    return transition


def csv_v5_append(file_name, json_data, data, systemname, p_status):
    # print("Start processing ", systemname)
    counter = 0
    # current_stage =
    # print("file_name:", file_name)
    it_stage = filtered_statuses_list_get(p_status)
    with open(file_name, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        counter = data_rows_prepare(
            json_data, data, systemname, it_stage, writer)
    print(systemname, " is accomplished counter=", counter)


def takeFourth(elem):
    return elem[4]

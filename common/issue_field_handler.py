import datetime
from atlassian import Jira
import json
from jsonpath_ng import jsonpath, parse

from json_util_v2 import read_json_file


def invalid_field(path_pattern, json_data):
    raise Exception("Invalid field")


def single_value_handler(path_pattern, json_data):
    gotdata = None
    # print(path_pattern)
    status_jsonpath_expr = parse(path_pattern)
    value = status_jsonpath_expr.find(json_data)
    if len(value) > 0:
        gotdata = value[0].value
        gotdata = not_avail_value_assign(gotdata)
        # # Date time value
        # gotdata = date_format_conversion(gotdata)

    else:
        gotdata = not_avail_value_assign(gotdata)
    # if path_pattern == "$.fields[*].customfield_13824[*].value":
    #     print(gotdata)

    return gotdata


def date_format_conversion(date_object, format_str):
    # if isinstance(date_object, datetime.datetime):
    date_time_obj = datetime.datetime.strptime(
        date_object.rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')
    # return date_time_obj.strftime('%d/%m/%Y')
    return date_time_obj.strftime(format_str)
    # else:
    #     return date_object


def list_of_values_handler(path_pattern, json_data):
    gotdata = None
    # print(path_pattern)
    if isinstance(path_pattern, list):
        for item in path_pattern:
            status_jsonpath_expr = parse(item)
            value = status_jsonpath_expr.find(json_data)
            if len(value) > 0:
                gotdata = value[0].value
            else:
                gotdata = not_avail_value_assign(gotdata)
            if item in get_change_request_types():
                gotdata = not_avail_value_assign(gotdata)
            else:
                gotdata = not_avail_value_assign(gotdata)
            if item in get_biz_benefits():
                gotdata = not_avail_value_assign(gotdata)
            else:
                gotdata = not_avail_value_assign(gotdata)
            if item in get_biz_priority():
                gotdata = not_avail_value_assign(gotdata)
            else:
                gotdata = not_avail_value_assign(gotdata)
            if item in get_biz_division():
                print(item)
                gotdata = not_avail_value_assign(gotdata)
            else:
                gotdata = not_avail_value_assign(gotdata)
            if item in get_bizexpect_timeline():
                gotdata = not_avail_value_assign(gotdata)
            else:
                gotdata = not_avail_value_assign(gotdata)
    return gotdata


def get_change_request_types():
    change_type_field_array = [
        "$.fields[*].customfield_13805[*].value",
        "$.fields[*].customfield_13806[*].value",
        "$.fields[*].customfield_13807[*].value"
    ]
    return change_type_field_array


def get_biz_benefits():
    biz_benefits = [
        "$.fields[*].customfield_13824",
        "$.fields[*].customfield_13867"
    ]
    return biz_benefits


def get_biz_priority():
    biz_priority = [
        "$.fields[*].customfield_13825[*].value",
        "$.fields[*].customfield_13870[*].value"
    ]
    return biz_priority


def get_biz_division():
    biz_division = [
        "$.fields[*].customfield_13827[*].value",
        "$.fields[*].customfield_13869[*].value"
    ]
    return biz_division


def get_bizexpect_timeline():
    bizexpect_timeline = [
        "$.fields[*].customfield_13826",
        "$.fields[*].customfield_13868"
    ]
    return bizexpect_timeline


def not_avail_value_assign(gotdata):
    if gotdata == 0 or gotdata == "" or gotdata == None:
        return "Not Available"
    return gotdata

# The better way:


def perform_operation(chosen_field, json_data, path_pattern):
    ops = {
        "key": single_value_handler,
        "summary": single_value_handler,
        "biz_benefits": list_of_values_handler,
        "changerequesttype": list_of_values_handler,
        "biz_priority": list_of_values_handler,
        "biz_division": list_of_values_handler,
        "bizexpect_timeline": list_of_values_handler,
        "created": single_value_handler,
        "updated": single_value_handler,
        "status": single_value_handler,
        "requestor": single_value_handler,
        "valid": single_value_handler,
        "proposed_to_bom": single_value_handler,
        "it_recommendation": single_value_handler,
        "proposed_date": single_value_handler,
        "bom_approval": single_value_handler,
        "approval_date": single_value_handler
    }
    # print(ops)
    chosen_operation_function = ops.get(chosen_field, invalid_field)

    # print(chosen_operation_function)

    return chosen_operation_function(path_pattern, json_data)


def jira_cr_extract(jql):
    jira = Jira(
        url='https://fecredit.atlassian.net',
        username='khoa.nguyen.24@fecredit.com.vn',
        password='AEqPCgn5b5BSOArR0Aqu612D')  # password is a generated Token
    issues = jira.jql_get_list_of_tickets(jql)
    json_object = json.dumps(issues, indent=4)
    json_data = json.loads(json_object)
    # print(json_data)
    return json_data


if __name__ == "__main__":
    jql = "project = BCA AND issuetype in (Refactor, Story) AND status not in (Done, Rejected) AND created >= 2022-04-01 AND created <= 2022-04-30 order by created DESC"
    data = read_json_file("parsing_paths_v3.json")
    for item in data:
        for json_item in jira_cr_extract(jql):
            if "biz_benefits" == item:
                print(data[item])
                print(perform_operation(item, json_item, data[item]))

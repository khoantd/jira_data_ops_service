
from typing import List
from common.json_util import *
# from json_util import *


def team_setting_retrieve(team_name, data):
    # print(data)
    if isinstance(data, list):
        for item in data:
            team_acct = item.get(team_name)
        if team_acct != "" or len(team_acct) > 0:
            return team_acct
        else:
            return "Not found"
    if isinstance(data, str):
        team_acct = data.get(team_name)


def jira_accounts_retrieve(config):
    data = read_json_file(config)
    return parse_json_v2("$.team_accounts", data)


def rpt_headers_retrieve(config):
    data = read_json_file(config)
    return parse_json_v2("$.rpt_headers_list", data)


def rpt_file_retrieve(config):
    data = read_json_file(config)
    return parse_json_v2("$.rpt_list", data)


def rpt_db_file_retrieve(config):
    data = read_json_file(config)
    return parse_json_v2("$.db_tables_list", data)


def paths_parsing_files_retrieve(config):
    # print(config-pattern)
    data = read_json_file(config)
    # print(parse_json_v2("$.path_parsing_patterns_list", data))
    return parse_json_v2("$.path_parsing_patterns_list", data)


def teams_retrieve(config):
    data = read_json_file(config)
    return parse_json_v2("$.teams_list", data)


def itsd_prj_retrieve(config):
    data = read_json_file(config)
    return parse_json_v2("$.itsd_prj_list", data)


def teams_jqls_list_retrieve(config):
    data = read_json_file(config)
    return parse_json_v2("$.jql_list", data)


def teams_fields_handling_list_retrieve(config):
    data = read_json_file(config)
    return parse_json_v2("$.fields_handling_list", data)


if __name__ == "__main__":
    print("acct_util.py")

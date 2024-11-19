import configparser
import json
import rule_engine
from common.json_util import read_json_file
from common.json_util import parse_json_v2
from common.s3_aws_util import config_file_read
from domain.conditions.condition_obj import Condition
from domain.rules.rule_obj import ExtRule
from common.conditions_enum import equation_operators, logical_operators
from common.util import cfg_read


def rules_set_cfg_read():
    json_data = read_json_file(
        f'{cfg_read("RULE", "file_name")}')
    parsed_data_main_node = parse_json_v2("$.rules_set", json_data)
    return parsed_data_main_node


def actions_set_cfg_read():
    return rule_actions_read(f'{cfg_read("RULE", "file_name")}')


def conditions_set_cfg_read():
    json_data = read_json_file(
        f'{cfg_read("CONDITIONS", "file_name")}')
    parsed_data_main_node = parse_json_v2("$.conditions_set", json_data)
    return parsed_data_main_node


def rules_set_setup(rules_set):
    conditionss_set = conditions_set_load()
    rule_exec_result_list = None
    rule_exec_result_list = rules_set_exec(rules_set, conditionss_set)
    return rule_exec_result_list


def rules_set_exec(rules_set, conditionss_set):
    rules_list = rules_set
    tmp_rule_exec_result_list = []
    for rule in rules_list:
        # print("rule",rule)
        tmp_rule_exec_result_list.append(rule_prepare(conditionss_set, rule))
    return tmp_rule_exec_result_list


def rule_prepare(conditionss_set, rule):
    rule_exec_result = {}
    tmp_rule = ExtRule(**rule)
    tmp_cond_concated_str = ""
    tmp_logical_operator = ""
    tmp_cond_ls = []
    if tmp_rule.type == 'complex':
        tmp_conditions = tmp_rule.conditions['items']
        # tmp_cond_concated_str=''
        for i in range(len(tmp_conditions)):
            # print(item)
            for cond in conditionss_set:
                # print("tmp_cond.condition_name",cond)
                if cond.condition_id == tmp_conditions[i]:
                    tmp_str = str(cond.attribute)+str(" ")+str(
                        equation_operators(cond.equation))+str(" ")+str(cond.constant)
                    tmp_cond_ls.append(tmp_str)
                    # print("tmp_str",tmp_str)
        tmp_logical_operator = logical_operators(tmp_rule.conditions['mode'])
        # print("tmp_logical_operator",tmp_logical_operator)

        tmp_cond_concated_str = f' {tmp_logical_operator} '.join(
            map(str, tmp_cond_ls))
        # print("tmp_cond_concated_str",tmp_cond_concated_str)
    elif tmp_rule.type == 'simple':
        # print("tmp_rule", tmp_rule)
        tmp_condition = tmp_rule.conditions['item']
        # print("tmp_conditions", tmp_conditions)
        for cond in conditionss_set:
            # print("cond", cond)
            tmp_str = None
            if cond.condition_id == tmp_condition:
                tmp_str = str(cond.attribute)+str(" ")+str(
                    equation_operators(cond.equation))+str(" ")+str(cond.constant)
                # tmp_cond_ls.append(tmp_str)
                # print("tmp_str", tmp_str)
        tmp_cond_concated_str = tmp_str
    rule_exec_result = {
        "priority": tmp_rule.priority,
        "rule_name": tmp_rule.rulename,
        "condition": tmp_cond_concated_str,
        "rule_point": tmp_rule.rulepoint,
        "action_result": tmp_rule.action_result,
        "weight": tmp_rule.weight
    }
    return rule_exec_result


def conditions_set_load():
    conditions_list = []
    loaded_conditions_set = conditions_set_cfg_read()
    # print("loaded_conditions_set", loaded_conditions_set)
    for item in loaded_conditions_set:
        # print("item",item)
        tmp_condition = Condition(**item)
        # print("tmp_condition.condition_name", tmp_condition.condition_name)
        conditions_list.append(tmp_condition)
    return conditions_list

# def rules_v2_exec(rule_cfg, data):
#     rules_list = []
#     rules_list.sort(key=sort_fn)
#     results = []
#     executed_rules = 0
#     sum = 0
#     # final_point = 0.0
#     rules_list = rules_setup(rules_set_from_s3_read(rule_cfg))
#     for rule in rules_list:
#         # print(rule)
#         result = rule_run(rule, data)
#         executed_rules = executed_rules+1
#         sum = sum+result["rule_point"]
#         results.append(result["action_result"])
#     tmp_str = str("".join(results))

#     tmp_action = rule_action_handle(
#         rule_actions_from_S3_read(rule_cfg), tmp_str)
#     # print("tmp_action:", tmp_action)
#     rs = {
#         "total_points": sum,
#         "pattern_result": tmp_str,
#         "action_recommendation": tmp_action
#     }
#     return rs


def rule_setup(rule, condition):
    tmp_rule = {
        "priority": rule["priority"],
        "rule_name": rule["rule_name"],
        "condition": condition,
        "rule_point": rule["rule_point"],
        "action_result": rule["action_result"],
        "weight": rule["weight"]
    }
    return tmp_rule


def condition_setup(rule):
    tmp_condition = []
    # print(rule["attribute"])
    tmp_condition.append(rule["attribute"])
    tmp_condition.append(equation_operators(rule["condition"]))
    tmp_condition.append(str(rule["constant"]))
    # print("tmp_condition:", tmp_condition)
    return " ".join(tmp_condition)


def rules_set_read(json_file):
    json_data = read_json_file(json_file)
    parsed_data_main_node = parse_json_v2("$.rules_set", json_data)
    # print(parsed_data_main_node)
    return parsed_data_main_node


def condition_set_read(json_file):
    json_data = read_json_file(json_file)
    parsed_data_main_node = parse_json_v2("$.conditions_set", json_data)
    # print(parsed_data_main_node)
    return parsed_data_main_node


def rules_set_from_s3_read(config_file):
    # json_data = read_json_file(json_file)
    # config_file = "rules_config/rules_config_v3.json"
    cfg_content = config_file_read("S3", config_file)
    parsed_data_main_node = parse_json_v2(
        "$.rules_set", json.loads(cfg_content))
    # print(parsed_data_main_node)
    return parsed_data_main_node


def rule_actions_read(json_file):
    json_data = read_json_file(json_file)
    # print("json_data",json_data)
    parsed_data_main_node = parse_json_v2("$.patterns", json_data)
    # print(parsed_data_main_node)
    return parsed_data_main_node


def rule_actions_from_S3_read(config_file):
    # json_data = read_json_file(json_file)
    cfg_content = config_file_read("S3", config_file)
    parsed_data_main_node = parse_json_v2(
        "$.patterns", json.loads(cfg_content))
    # print(parsed_data_main_node)
    return parsed_data_main_node


def rule_action_handle(actions_list, data):
    # print("data:", data)
    for key, value in actions_list.items():
        if key == data:
            # print(value)
            return value


def rule_run(rule, data):
    # print("rule",rule)
    tmp_action = ""
    tmp_weight = 0
    tmp_point = 0
    try:
        print("rule[\"condition\"]", rule["condition"])
        l_rule = rule_engine.Rule(rule["condition"])
        rs = l_rule.matches(data)
        # print(rs)
        # print(rule['rule_point'])
        if rs == True:
            tmp_action = str(rule["action_result"])
            tmp_point = float(rule['rule_point'])
            tmp_weight = float(rule['weight'])
        else:
            tmp_action = '-'
    except:
        tmp_action = '-'
    return {
        "action_result": tmp_action,
        "rule_point": tmp_point,
        "weight": tmp_weight
    }


def sort_fn(e):
    return e['priority']

from common.json_util import *
from common.conditions_enum import *
from common.rule_engine_util import *


def rules_exec(data):
    rules_list = []
    rules_list.sort(key=sort_fn)
    results = []
    executed_rules = 0
    sum = 0
    rules_list = rules_set_setup(rules_set_cfg_read())
    for rule in rules_list:
        print("rule", rule)
        result = rule_run(rule, data)
        executed_rules = executed_rules+1
        sum = sum + (float(result["rule_point"]) * float(result["weight"]))
        results.append(result["action_result"])
    tmp_str = str("".join(results))
    tmp_action = rule_action_handle(actions_set_cfg_read(), tmp_str)
    rs = {
        "total_points": sum,
        "pattern_result": tmp_str,
        "action_recommendation": tmp_action
    }
    return rs


if __name__ == "__main__":
    print("main.py")

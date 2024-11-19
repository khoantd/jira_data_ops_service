from domain.jsonobj import JsonObject
from domain.actions.action_obj import Action


class Rule(JsonObject):
    def __init__(self, id: str, rule_name: str, conditions: list, description: str, result: str):
        super().__init__()
        self.__id = id
        self.__rulename = rule_name
        self.__description = description
        self.__conditions = conditions
        self.__result = result
        self._json_obj = self.json_obj_print()

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, id):
        self._json_obj["id"] = id
        self.__id = id

    @property
    def rulename(self):
        return self.__rulename

    @rulename.setter
    def rulename(self, rulename):
        self._json_obj["rulename"] = rulename
        self.__rulename = rulename

    @property
    def description(self):
        return self.__description

    @description.setter
    def description(self, description):
        self._json_obj["description"] = description
        self.__description = description

    @property
    def conditions(self):
        return self.__conditions

    @conditions.setter
    def conditions(self, conditions):
        self._json_obj["conditions"] = conditions
        self.__conditions = conditions

    @property
    def result(self):
        return self.__result

    @result.setter
    def result(self, result):
        self._json_obj["result"] = result
        self.__result = result

    def get_json_data(self):
        return self._json_obj


class ExtRule(Rule):
    def __init__(self, id: str, rule_name: str,  conditions: list, description: str, result: str, rule_point: float, weight: float, priority: int, type:str,action_result:str):
        super().__init__(id, rule_name, description, conditions, result)
        self.__rule_point = rule_point
        self.__weight = weight
        self.__priority = priority
        self.__conditions=conditions
        self.__type=type
        self.__action_result=action_result

    @property
    def rulepoint(self):
        return self.__rule_point

    @rulepoint.setter
    def rulepoint(self, rule_point):
        self._json_obj["rule_point"] = rule_point
        self.__rule_point = rule_point

    @property
    def conditions(self):
        return self.__conditions

    @conditions.setter
    def conditions(self, conditions):
        self._json_obj["conditions"] = conditions
        self.__conditions = conditions

    
    @property
    def weight(self):
        return self.__weight

    @weight.setter
    def weight(self, weight):
        self._json_obj["weight"] = weight
        self.__weight = weight

    @property
    def priority(self):
        return self.__priority

    @priority.setter
    def priority(self, priority):
        self._json_obj["priority"] = priority
        self.__priority = priority
        
    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, type):
        self._json_obj["type"] = type
        self.__type = type
        
    @property
    def action_result(self):
        return self.__action_result

    @action_result.setter
    def action_result(self, action_result):
        self._json_obj["action_result"] = action_result
        self.__action_result = action_result

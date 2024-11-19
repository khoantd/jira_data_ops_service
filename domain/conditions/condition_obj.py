from domain.jsonobj import JsonObject


class Condition(JsonObject):
    def __init__(self,condition_id:str, condition_name: str, attribute: str, equation: str, constant: str):
        super().__init__()
        self.__condition_id = condition_id
        self.__condition_name = condition_name
        self.__attribute = attribute
        self.__equation = equation
        self.__constant = constant
        self.__json_obj = self.json_obj_print()

    @property
    def condition_id(self):
        return self.__condition_id

    @condition_id.setter
    def condition_id(self, condition_id):
        self.__json_obj["condition_id"] = condition_id
        self.__condition_id = condition_id


    @property
    def condition_name(self):
        return self.__condition_name

    @condition_name.setter
    def condition_name(self, condition_name):
        self.__json_obj["condition_name"] = condition_name
        self.__condition_name = condition_name

    @property
    def attribute(self):
        return self.__attribute

    @attribute.setter
    def attribute(self, attribute):
        self.__json_obj["attribute"] = attribute
        self.__attribute = attribute

    @property
    def equation(self):
        return self.__equation

    @equation.setter
    def equation(self, equation):
        self.__json_obj["equation"] = equation
        self.__equation = equation

    @property
    def constant(self):
        return self.__constant

    @constant.setter
    def constant(self, constant):
        self.__json_obj["constant"] = constant
        self.__constant = constant

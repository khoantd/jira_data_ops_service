class JsonObject:
    def __init__(self):
        self._json_obj = {}

    def json_obj_print(self):
        return self._json_obj

    def set_json_data(self, json_data):
        self._json_obj = json_data

from common.json_util import parse_json_v2, read_json_file


CONFIG_FILE_PATH = 'config/message_templates.json'


def message_template_file_config_load():
    data = read_json_file(CONFIG_FILE_PATH)
    # print("data", data)
    return parse_json_v2("$.message_list", data)


def message_template_retrieve(template_id):
    data = message_template_file_config_load()
    for item in data:  # type: ignore
        if item['templateId'] == template_id:
            return item['body']

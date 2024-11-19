# from asyncio.windows_events import NULL
import json
from jsonpath_ng import jsonpath, parse


def parse_json(path_pattern, json_data):
    data = change_type_parse(path_pattern, json_data)
    return data


def change_type_parse(path_pattern, json_data):
    gotdata = "Not Available"
    status_jsonpath_expr = parse(path_pattern)
    value = status_jsonpath_expr.find(json_data)
    change_type_field_array = [
        "$.fields[*].customfield_13805[*].value",
        "$.fields[*].customfield_13806[*].value",
        "$.fields[*].customfield_13807[*].value"
    ]
    try:
        gotdata = value[0].value
        gotdata = not_avail_change_type_assign(
            path_pattern, gotdata, change_type_field_array)
    except IndexError:
        gotdata = not_avail_change_type_assign(
            path_pattern, gotdata, change_type_field_array)
    return gotdata


def json_to_row_data_convert(pasring_path_file, data):
    parsing_path_data = read_json_file(pasring_path_file)
    rows = []
    for rec in data:
        row = []
        for json_path_item in parsing_path_data:
            row.append(parse_json_v2(parsing_path_data[json_path_item], rec))
        rows.append(row)
    return rows


def not_avail_change_type_assign(path_pattern, gotdata, change_type_field_array):
    if path_pattern in change_type_field_array and gotdata == 0:
        gotdata = "Not Available"
    return gotdata


def parse_json_v2(path_pattern, json_data):
    gotdata = 0
    status_jsonpath_expr = parse(path_pattern)
    value = status_jsonpath_expr.find(json_data)
    try:
        gotdata = value[0].value
    except IndexError:
        gotdata = 0
    return gotdata


def parse_json_v3(path_pattern, json_data):
    gotdata = 0
    status_jsonpath_expr = parse(path_pattern)
    value = status_jsonpath_expr.find(json_data)
    try:
        gotdata = value[0].value
    except IndexError:
        gotdata = 0
    return gotdata


def biz_benefits_check(p_input_paragraph):
    # result = p_input_paragraph.find(p_input_string)
    # print(p_input_paragraph)
    str = "Financial Impact:_____, Or\n\nNumber of impacted customers/users:______, Or\n\nOthers:______"
    result = ""
    if p_input_paragraph == None:
        result = "Not Available"
        # print("Not Available")
    else:
        if str == p_input_paragraph:
            result = "Not Available"
            # print("Not Available")
        else:
            result = p_input_paragraph
    return result


def read_json_file(file_path):
    # print(file_path)
    f = open(file_path)
    # print(f)
    data = json.load(f)
    return data


def create_json_file(json_string, file_name):
    # Serializing json
    # json_string.replace('][', ',')
    # str = json_string
    # str = str.replace('][', ',')
    json_object = json.dumps(json_string, ensure_ascii=False, indent=4)
    # json_object.replace('][', ',')
    # print(json_string)
    # Writing to sample.json
    with open(f"{file_name}", "w") as outfile:
        outfile.write(json_object.replace('][', ','))


def json_print(data):
    ls = []
    for key, value in data.items():
        rc = {
            key: value
        }
        ls.append(rc)
        # print(key, ":", value)
    return ls


def json_key_get(data, key_search):
    ls = []
    for key, value in data.items():
        if value == key_search:
            ls.append(key)
        else:
            pass
    return ls


def json_value_get(data, key_search):
    ls = []
    for key, value in data.items():
        if key == key_search:
            ls.append(value)
        else:
            pass
    return ls


if __name__ == "__main__":
    # json_object = read_json_file(
    #     "cr_type_update/data/input/parsing_paths_v2.json")
    json_object = read_json_file(
        "../config/jira_cr_statuses_obj.json")
    print(json_print(json_object))
    print(json_key_get(json_object, '3. In Development'))
    print(json_key_get(json_object, '4. UAT'))
    # print(json_object)
    # json_data = json.loads(json_object)

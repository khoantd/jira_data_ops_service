
from common.excel_file_reader import excel_file_read, specific_columns_by_value_extract, headers_extract
from common.excel_file_writer import excel_file_write
import re

from common.sqlite_util import create_connection
from common.sqlite_util import query_exec
# import pandas as pd
# import glob


def excepted_cases_remove(input_data_1, input_data_2, headers):
    data_rs = []
    for i, j in input_data_1.iterrows():
        l_ls_rs = []
        for header in headers:
            l_ls_rs.append(j[header])
        data_rs.append(l_ls_rs)
        for j in data_rs:
            for i in input_data_2:
                str_1 = i[1]
                str_2 = j[1]
                if str_1 == str_2:
                    data_rs.remove(j)
    return data_rs


def table_metadata_get(db_name, table_name):
    sql_stmt = f"SELECT name, sql FROM sqlite_master WHERE name = \"{table_name}\" ORDER BY name"
    row_rs = None
    with create_connection(db_name) as conn:
        rows = query_exec(
            conn, sql_stmt)
        for row in rows:
            if len(text_from_doble_quotes(row[1])) > 0:
                row_rs = text_from_doble_quotes(row[1])
    return row_rs


def text_from_doble_quotes(str):
    return re.findall(r'"([^"]*)"', str)


def crs_exception_exclude(input_file_1, input_file_2, column_name, value_check, key_column, extract_column):
    data_1 = excel_file_read(input_file_1)
    data_2 = excel_file_read(input_file_2)
    header_1 = headers_extract(input_file_1)
    header_2 = headers_extract(input_file_2)
    col_index_1 = extract_column.index(column_name)
    col_index_2 = extract_column.index(key_column)
    print(col_index_1, col_index_2)
    data_rs = []
    l_ecepted_cases = specific_columns_by_value_extract(
        data_2, header_2[0], value_check, header_2)
    data_rs = excepted_cases_remove(data_1, l_ecepted_cases, header_1)
    return data_rs


def excel_files_merge(list_of_files, output_file):
    for excl_file in list_of_files:
        excl_merged = excl_merged.append(
            excl_file, ignore_index=True)
    excl_merged.to_excel(output_file, index=False)


def excel_nan_data_remove(data, columns):
    output_data = []
    for item in columns:
        data.dropna(subset=[item], inplace=True)
    for rec in data.iterrows():
        l_data = []
        for i in range(len(rec[1])):
            l_data.append(rec[1][i])
        output_data.append(l_data)
    return output_data


def excel_row_data_convert(data):
    output_data = []
    # for item in columns:
    #     data.dropna(subset=[item], inplace=True)
    for rec in data.iterrows():
        l_data = []
        for i in range(len(rec[1])):
            l_data.append(rec[1][i])
        output_data.append(l_data)
    return output_data


def excel_files_batch_process(operation_name, files_list, file_output, columns_list):
    if operation_name == "late_cr_feedback_files_merging":
        l_g_arr = []
        for file in files_list:
            print(file)
            data = excel_nan_data_remove(excel_file_read(file), columns_list)
            for item in data:
                l_g_arr.append(item)
        excel_file_write(file_output, l_g_arr)
    return "Success"


def table_row_convert(db_name, table_name, data):
    metdata_table = table_metadata_get(db_name,
                                       table_name)
    print(metdata_table)
    dic_item_list = []
    data = excel_row_data_convert(
        excel_file_read(data))
    for item in data:
        rec_dict = dict(zip(metdata_table, item))
        dic_item_list.append(rec_dict)
        print(rec_dict)
    return dic_item_list


if __name__ == "__main__":
    # data = crs_exception_exclude("../data/output/Late_JIRA_CR_list.xlsx",
    #                              "../data/input/Late JIRA_CR_list_v2_Tai.xlsx", "system_name", ["Pega CSM"], "key", ["system_name", "key"])
    # excel_file_write("../data/output/Filtered_CRs.xlsx", data)
    # headers = headers_extract("../data/input/Late JIRA_CR_list_v2_Tai.xlsx")
    # print(headers[0])
    files_list = ["../data/input/feedback/Late JIRA_CR_list_v2_Tai.xlsx",
                  "../data/input/feedback/Late JIRA_CR_list_v2 - IA.xlsx",
                  "../data/input/feedback/Late JIRA_CR_list_v2_25Apr_LOSBAU.xlsx",
                  "../data/input/feedback/VYMO of Late JIRA_CR_list_v2.xlsx",
                  "../data/input/feedback/Late JIRA_CR_list_v2_ROBO_SHIELD.xlsx",
                  "../data/input/feedback/Late JIRA_CR_list_v2_CMS.xlsx",
                  "../data/input/feedback/Late JIRA_CR_list_v2_Pega Collection.xlsx"]
    output_file = "../data/output/Excluded_NAN_Data.xlsx"
    columns_list = [
        "Reason", "Next Actions"]
    print(excel_files_batch_process(
        "late_cr_feedback_files_merging", files_list, output_file, columns_list))



from common.data_transform import excel_row_data_convert
from common.sqlite_util import create_connection
from common.data_transform import excel_nan_data_remove
from common.excel_file_reader import excel_file_read
from common.excel_file_writer import excel_file_write
from common.sqlite_util import create_table
from common.data_transform import table_metadata_get


create_table_stmt = """CREATE TABLE IF NOT EXISTS long_pending_jira_issue_tracking (
    "SystemName" text NOT NULL,
    "IssueId" text PRIMARY KEY,
    "Summary" text NOT NULL,
    "CreatedMonth" INTEGER NOT NULL,
    "CreatedYear" INTEGER NOT NULL,
    "AgeTillExportingDate" INTEGER NOT NULL,
    "OriginalStatus" text NOT NULL,
    "BusinessStatus" text NOT NULL,
    "UnifiedITStatus" text NOT NULL,
    "Reason" text,
    "NextActions" text
);"""

insert_record_stmt = """
    INSERT INTO long_pending_jira_issue_tracking VALUES (?,?,?,?,?,?,?,?,?,?,?)
"""


def excel_files_to_sqlite_process(operation_name, files_list, file_output, columns_list):
    if operation_name == "late_cr_feedback_files_merging":
        l_g_arr = []
        for file in files_list:
            print(file)
            data = excel_nan_data_remove(excel_file_read(file), columns_list)
            for item in data:
                l_g_arr.append(item)
        excel_file_write(file_output, l_g_arr)
    return "Success"


def long_pending_jira_issues_table_init(db_name, create_table_stmt):
    con = create_connection(db_name)
    # "../data/input/db/jira_db.sqlite3"
    create_table(con, create_table_stmt)


def excel_row_to_table_row_convert(db_name, table_name, data):
    metdata_table = table_metadata_get(db_name,
                                       table_name)
    # print(metdata_table)
    dic_item_list = []
    data = excel_row_data_convert(
        excel_file_read(data))
    for item in data:
        rec_dict = dict(zip(metdata_table, item))
        dic_item_list.append(rec_dict)
        # print(rec_dict)
    return dic_item_list


def csv_row_to_table_row_convert(db_name, table_name, data):
    metdata_table = table_metadata_get(db_name,
                                       table_name)
    # print("metdata_table", metdata_table)
    dic_item_list = []
    for item in data:
        rec_dict = dict(zip(metdata_table, item))
        dic_item_list.append(rec_dict)
        # print(rec_dict)
    return dic_item_list


if __name__ == "__main__":
    # db location: "../data/input/db/jira_db.sqlite3",
    # table name: "long_pending_jira_issue_tracking"
    # input data: "../data/input/feedback/Late JIRA_CR_list_v2_Tai.xlsx"
    data = excel_row_to_table_row_convert("../data/input/db/jira_db.sqlite3", "long_pending_jira_issue_tracking",
                                          "../data/input/feedback/Late JIRA_CR_list_v2_Tai.xlsx")
    print(data)

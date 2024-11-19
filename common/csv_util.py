import csv
from csv import writer
from csv import reader
from csv import DictReader
from csv import DictWriter
import datetime
from operator import le
import os

import pytz

from common.jira_util import issue_data_extract
from common.biz_cal import *

from common.util import biz_days_btwn_days_calculate
from common.json_util import read_json_file
import rule_engine


def ReadCsv(filename, skipheader=False):
    records = []
    with open(filename, newline='') as csv_file:
        reader = csv.reader(csv_file)
        if skipheader == True:
            next(reader, None)  # skip reading header
        for record in reader:
            records.append(record)
    return records


def GetCsvHeader(filename):
    records = ReadCsv(filename, False)
    list_of_column_names = []
    for record in records:
        list_of_column_names = record
        print(record)
        break
    return list_of_column_names


def add_column_in_csv(input_file, output_file, transform_row):
    """ Append a column in existing csv using csv.reader / csv.writer classes"""
    # Open the input_file in read mode and output_file in write mode
    with ReadCsv(input_file) as read_obj, open(output_file, 'w', newline='') as write_obj:
        # Create a csv.reader object from the input file object
        # csv_reader = reader(read_obj)
        # Create a csv.writer object from the output file object
        csv_writer = writer(read_obj)
        # Read each row of the input csv file as list
        for row in read_obj:
            # Pass the list / row in the transform function to add column text for this row
            transform_row(row, read_obj.line_num)
            # Write the updated row / list to the output file
            csv_writer.writerow(row)


def add_numbering_column_to_csv(input_file, output_file):
    """ Append a column in existing csv using csv.reader / csv.writer classes"""
    # Open the input_file in read mode and output_file in write mode
    with open(input_file, 'r') as read_obj, open(output_file, 'w', newline='') as write_obj:
        # Create a csv.reader object from the input file object
        csv_reader = DictReader(read_obj)
        # Create a csv.writer object from the output file object
        csv_writer = DictWriter(write_obj, fieldnames=csv_reader.fieldnames)
        # Read each row of the input csv file as list
        counter = 1
        for row in csv_reader:
            # Pass the list / row in the transform function to add column text for this row
            row.insert(0, counter)
            counter += 1
            # Write the updated row / list to the output file
            csv_writer.writerow(row)


def add_validation_column_to_csv(output_path, input_file, output_file):
    """ Append a column in existing csv using csv.reader / csv.writer classes"""
    # Open the input_file in read mode and output_file in write mode
    with open(f"{output_path}{input_file}", 'r') as read_obj, open(f"{output_path}{output_file}", 'w', newline='') as write_obj:
        # Create a csv.reader object from the input file object
        csv_reader = DictReader(read_obj)
        headers = csv_reader.fieldnames
        # headers = []
        total_column = len(headers)
        headers.insert(total_column, "validation_result")
        headers.insert(total_column+1, "numbering")
        headers.insert(total_column+2, "no_of_errors")
        # Create a csv.writer object from the output file object
        csv_writer = DictWriter(write_obj, fieldnames=headers)
        # Read each row of the input csv file as list
        counter = 1
        csv_writer.writeheader()
        for row in csv_reader:
            # Pass the list / row in the transform function to add column text for this row
            row.update({"numbering": counter})
            row = fields_validate(row)
            counter += 1
            # Write the updated row / list to the output file
            csv_writer.writerow(row)
    return {
        "output_path": f"{output_path}",
        "file_name": f"{output_file}"
    }


def add_modified_day_column_to_csv(output_path, input_file, p_output_file=""):
    """ Append a column in existing csv using csv.reader / csv.writer classes"""
    # Open the input_file in read mode and output_file in write mode
    output_file = ""
    if p_output_file == "":
        output_file = f"{input_file.replace('.csv','')}_modified.csv"
    with open(f"{output_path}{input_file}", 'r') as read_obj, open(f"{output_path}{output_file}", 'w', newline='') as write_obj:
        # Create a csv.reader object from the input file object
        csv_reader = DictReader(read_obj)
        headers = csv_reader.fieldnames
        # headers = []
        total_column = len(headers)
        headers.insert(total_column, "modified_date")
        headers.insert(total_column+1, "numbering")
        # Create a csv.writer object from the output file object
        csv_writer = DictWriter(write_obj, fieldnames=headers)
        # Read each row of the input csv file as list
        counter = 1
        csv_writer.writeheader()
        for row in csv_reader:
            # Pass the list / row in the transform function to add column text for this row
            row.update({"numbering": counter})
            row = modified_date_add(row, "modified_date")
            counter += 1
            # Write the updated row / list to the output file
            csv_writer.writerow(row)
    return {
        "output_path": f"{output_path}",
        "file_name": f"{output_file}"
    }


def add_deliquency_column_to_csv(output_path, input_file, output_file):
    """ Append a column in existing csv using csv.reader / csv.writer classes"""
    # Open the input_file in read mode and output_file in write mode
    with open(f"{output_path}{input_file}", 'r') as read_obj, open(f"{output_path}{output_file}", 'w', newline='') as write_obj:
        # Create a csv.reader object from the input file object
        csv_reader = DictReader(read_obj)
        headers = csv_reader.fieldnames
        # headers = []
        total_column = len(headers)
        headers.insert(total_column+5, "suggested_start_date")
        headers.insert(total_column+6, "suggested_end_date")
        # headers.insert(total_column+7, "remarks")
        headers.insert(total_column+2, "deliquency_90days")
        headers.insert(total_column+3, "deliquency_bomc")
        headers.insert(total_column+4, "age_since_approval_date")
        headers.insert(total_column+1, "numbering")
        # Create a csv.writer object from the output file object
        csv_writer = DictWriter(write_obj, fieldnames=headers)
        # Read each row of the input csv file as list
        counter = 1
        csv_writer.writeheader()
        for row in csv_reader:
            # Pass the list / row in the transform function to add column text for this row
            if row["bom_decision"] in ["Approved", "Approved by Department"]:
                row.update({"numbering": counter})
                row = deliquency_row_add(row)
                counter += 1
                csv_writer.writerow(row)
    return {
        "output_path": f"{output_path}",
        "file_name": f"{output_file}"
    }


def add_analysis_columns_to_csv(output_path, input_file, output_file):
    """ Append a column in existing csv using csv.reader / csv.writer classes"""
    # Open the input_file in read mode and output_file in write mode
    with open(f"{output_path}{input_file}", 'r') as read_obj, open(f"{output_path}{output_file}", 'w', newline='') as write_obj:
        # Create a csv.reader object from the input file object
        csv_reader = DictReader(read_obj)
        headers = csv_reader.fieldnames
        # headers = []
        total_column = len(headers)
        headers.insert(total_column+2, "bom_decision")
        headers.insert(total_column+3, "bom_approval_date")
        headers.insert(total_column+1, "numbering")
        # Create a csv.writer object from the output file object
        csv_writer = DictWriter(write_obj, fieldnames=headers)
        # Read each row of the input csv file as list
        counter = 1
        parsed_data = None
        csv_writer.writeheader()
        for row in csv_reader:
            # print(row)
            # Pass the list / row in the transform function to add column text for this row
            parsed_data = issue_data_extract(
                row["key"], "IT CM", ['bom_decision', 'bom_approval_date'])
            # if row["bom_decision"] in ["Approved", "Approved by Department"]:
            row.update({"numbering": counter})
            row.update({"bom_decision": parsed_data[0]})
            row.update({"bom_approval_date": parsed_data[1]})
            # row = deliquency_row_add(row)
            counter += 1
            csv_writer.writerow(row)
    return {
        "output_path": f"{output_path}",
        "file_name": f"{output_file}"
    }


def add_review_column_to_csv(output_path, input_file, output_file):
    """ Append a column in existing csv using csv.reader / csv.writer classes"""
    # Open the input_file in read mode and output_file in write mode
    with open(f"{output_path}{input_file}", 'r') as read_obj, open(f"{output_path}{output_file}", 'w', newline='') as write_obj:
        # Create a csv.reader object from the input file object
        csv_reader = DictReader(read_obj)
        headers = csv_reader.fieldnames
        # headers = []
        total_column = len(headers)
        headers.insert(total_column+5, "suggested_start_date")
        headers.insert(total_column+6, "suggested_end_date")
        headers.insert(total_column+7, "result")
        headers.insert(total_column+8, "efforts_review")
        headers.insert(total_column+2, "deliquency_90days")
        headers.insert(total_column+3, "deliquency_bomc")
        headers.insert(total_column+4, "age_since_approval_date")
        headers.insert(total_column+1, "numbering")
        # Create a csv.writer object from the output file object
        csv_writer = DictWriter(write_obj, fieldnames=headers)
        # Read each row of the input csv file as list
        counter = 1
        csv_writer.writeheader()
        for row in csv_reader:
            # Pass the list / row in the transform function to add column text for this row
            if row["bom_decision"] in ["Approved", "Approved by Department"]:
                row.update({"numbering": counter})
                row = review_row_add(row)
                print("row:", row)
                counter += 1
                csv_writer.writerow(row)
    return {
        "output_path": f"{output_path}",
        "file_name": f"{output_file}"
    }


def violated_rules_to_csv(output_path, input_file, output_file):
    with open(f"{output_path}{input_file}", 'r') as read_obj, open(f"{output_path}{output_file}", 'w', newline='') as write_obj:
        # Create a csv.reader object from the input file object
        csv_reader = DictReader(read_obj)
        # headers = csv_reader.fieldnames
        headers = ["key", "biz_division",
                   "system_name", "error_code", "error_msg", "updated_date"]
        # headers = []
        # Create a csv.writer object from the output file object
        csv_writer = DictWriter(write_obj, fieldnames=headers)
        # Read each row of the input csv file as list
        counter = 1
        csv_writer.writeheader()
        row = {}
        for row_reader in csv_reader:
            str = row_reader["validation_result"]
            arr = str.split(";")
            if len(arr) > 0 and arr[0] != "Cleaned":
                for i in range(len(arr)):
                    err_code = arr[i].split(":")[0]
                    row.update({"key": row_reader["key"]})
                    row.update({"biz_division": row_reader["biz_division"]})
                    row.update({"system_name": row_reader["system_name"]})
                    row.update({"error_code": err_code})
                    row.update({"error_msg": arr[i]})
                    row.update({"updated_date": row_reader["updated_date"]})
                    # print(row)
                    csv_writer.writerow(row)
            # row.update({"numbering": counter})
            # row = fields_validate(row)
            # counter += 1
            # Write the updated row / list to the output file
            # csv_writer.writerow(row)
    return {
        "output_path": f"{output_path}",
        "file_name": f"{output_file}"
    }


def deliquency_summary_to_csv(output_path, input_file, output_file):
    with open(f"{output_path}{input_file}", 'r') as read_obj, open(f"{output_path}{output_file}", 'w', newline='') as write_obj:
        # Create a csv.reader object from the input file object
        csv_reader = DictReader(read_obj)
        # headers = csv_reader.fieldnames
        headers = ["month", "year",
                   "inprogress_crs", "late_90days_crs", "new_crs", "created"]
        # headers = []
        # Create a csv.writer object from the output file object
        csv_writer = DictWriter(write_obj, fieldnames=headers)
        # Read each row of the input csv file as list
        counter = 1
        csv_writer.writeheader()
        row = {}
        new_crs_in_curr_month_cnt = 0
        inprogress_crs_till_curr_month_cnt = 0
        late_crs_till_curr_month_cnt = 0
        current_date = datetime.date.today()
        curr_month_of_creation = current_date.strftime("%m")
        curr_year_of_creation = current_date.strftime("%Y")
        for row_reader in csv_reader:
            # Logic fo counting new crs created within current month
            cutoff_time_date = datetime.datetime.strptime(
                row_reader["cutoff_time"], '%Y-%m-%d').date()
            month_of_creation = row_reader["month"]
            year_of_creation = row_reader["year"]
            print(cutoff_time_date.strftime("%m"))
            print(cutoff_time_date.strftime("%Y"))
            if int(curr_year_of_creation) == int(year_of_creation) and int(curr_month_of_creation) == int(month_of_creation):
                if row_reader["bom_decision"] in ["Approved", "Approved by Department"]:
                    new_crs_in_curr_month_cnt = new_crs_in_curr_month_cnt+1
            # Logic fo counting inprogress CRs till current month
            if row_reader["biz_status"] == "Open" and row_reader["bom_decision"] in ["Approved", "Approved by Department"]:
                print(row_reader["biz_status"])
                print(row_reader["bom_decision"])
                inprogress_crs_till_curr_month_cnt = inprogress_crs_till_curr_month_cnt+1
            # Logic fo counting late CRs till current month
            if int(row_reader["deliquency_90days"]) == 1:
                late_crs_till_curr_month_cnt = late_crs_till_curr_month_cnt+1
            # row.update({"numbering": counter})
            # row = fields_validate(row)
            # counter += 1
            # Write the updated row / list to the output file
            # csv_writer.writerow(row)
        row.update({"inprogress_crs": inprogress_crs_till_curr_month_cnt})
        row.update({"new_crs": new_crs_in_curr_month_cnt})
        row.update({"late_90days_crs": late_crs_till_curr_month_cnt})
        row.update({"month": curr_month_of_creation})
        row.update({"year": curr_year_of_creation})
        row.update({"created": current_date})
        # print(row)
        csv_writer.writerow(row)
    return {
        "output_path": f"{output_path}",
        "file_name": f"{output_file}"
    }


def index_checksum_to_csv(output_path, input_file, output_file):

    # try:
    #     current_date = datetime.datetime.now().strftime('%d-%m-%Y')
    #     if check_csv_empty(f'{output_path}{output_file}_{current_date}') == True:
    #         data_insert(output_path, input_file,
    #                     f'{output_file}_{current_date}', 'w')
    # except:
    #     data_insert(output_path, input_file,
    #                 f'{output_file}_{current_date}', 'w')

    try:
        if check_csv_empty(f'{output_path}{output_file}') == True:
            data_insert(output_path, input_file, output_file, 'w')
        else:
            data_insert(output_path, input_file, output_file, 'a+')
    except FileNotFoundError:
        data_insert(output_path, input_file, output_file, 'w')

    return {
        "output_path": f"{output_path}",
        "file_name": f"{output_file}"
    }


def index_checksum_to_csv_per_day(output_path, input_file, output_file):

    try:
        current_date = datetime.datetime.now().strftime('%d-%m-%Y')
        if check_csv_empty(f'{output_path}{output_file}_{current_date}') == True:
            data_insert(output_path, input_file,
                        f'{output_file}_{current_date}', 'w')
    except:
        data_insert(output_path, input_file,
                    f'{output_file}_{current_date}', 'w')

    return {
        "output_path": f"{output_path}",
        "file_name": f"{output_file}_{current_date}"
    }


def data_insert(output_path, input_file, output_file, mode):
    with open(f"{output_path}{input_file}", 'r') as read_obj, open(f"{output_path}{output_file}", mode, newline='') as write_obj:
        csv_reader = DictReader(read_obj)
        headers = ["system_name",
                   "key",
                   "created_date", "day", "month",
                   "year", "new", "closed", "in_progress", "on_hold", "can_rej"]
        csv_writer = DictWriter(write_obj, fieldnames=headers)
        if mode == "w":
            csv_writer.writeheader()
        current_date = datetime.datetime.now()
        it_sys_list = read_json_file(
            "./config-pattern/it_systems_list.json")["it_systems_list"]
        # print(it_sys_list)
        print(len(it_sys_list))
        for row_reader in csv_reader:
            internal_row = {}
            new_cnt = 0
            closed_cnt = 0
            in_progress_cnt = 0
            hold_cnt = 0
            can_rej = 0
            for item in range(len(it_sys_list)):
                if it_sys_list[item] == row_reader["system_name"]:
                    internal_row.update({"system_name": it_sys_list[item]})
                    internal_row.update({"key": row_reader["key"]})
                    status = row_reader["it_status"]
                    if status in ["0. New/Open"]:
                        new_cnt = new_cnt+1
                    elif status in ["7. Hold"]:
                        hold_cnt = hold_cnt+1
                    elif status in ["6. Cancel or Rejected"]:
                        can_rej = can_rej+1
                    elif status in ["5. Done"]:
                        closed_cnt = closed_cnt+1
                    else:
                        in_progress_cnt = in_progress_cnt+1
                    internal_row.update(
                        {"created_date": current_date.strftime('%d-%m-%Y')})
                    internal_row.update(
                        {"day": current_date.strftime('%d')})
                    internal_row.update(
                        {"month": current_date.strftime('%m')})
                    internal_row.update(
                        {"year": current_date.strftime('%Y')})
                    internal_row.update({"new": new_cnt})
                    internal_row.update({"closed": closed_cnt})
                    internal_row.update({"in_progress": in_progress_cnt})
                    internal_row.update({"on_hold": hold_cnt})
                    internal_row.update({"can_rej": can_rej})
                    csv_writer.writerow(internal_row)


def modified_date_add(row, column_name):
    tz_VN = pytz.timezone('Asia/Ho_Chi_Minh')
    datetime_VN = datetime.datetime.now(tz_VN)
    # updated_date = datetime.datetime.now()
    row.update({f"{column_name}": datetime_VN})
    return row


def fields_validate(row):
    validation_rs = []
    # num = int(row["days_since_updated"])
    # Start of the change 02/07/2022
    updated_date = row["updated_date"]
    converted_time = datetime.datetime.strptime(
        updated_date, "%Y-%m-%d")
    local = datetime.datetime.now()
    num = biz_days_btwn_days_calculate(converted_time, local)
    # End of the change 02/07/2022
    # adding error counter
    error_counter = 0
    requestor = row["requestor"]
    assignee = row["assignee"]
    bom_decision = row["bom_decision"]
    biz_benefits = row["biz_benefits"]
    biz_priority = row["biz_priority"]
    biz_division = row["biz_division"]
    bizexpect_timeline = row["bizexpect_timeline"]
    # validation_result = row["validation_result"]
    # if validation_result == None:
    #     validation_result = ""
    if (num >= 10 and (requestor == assignee)):
        # print("validation_result;", validation_result)
        if bom_decision == "Deferred":
            validation_rs.append(
                "Violated_R3: deferred_pending_at_requestor_10_working_days")
        else:
            validation_rs.append(
                "Violated_R1: pending_at_requestor_10_working_days")
        print("validation_result:", validation_rs)
        error_counter += 1
    if (num >= 90):
        validation_rs.append("Violated_R2: age_greater_than_90_days")
        # print("validation_result;", validation_result)
        error_counter += 1
    # if bom_decision == "Deferred" and num >= 10 and (requestor == assignee):
    #     validation_rs.append("Violated_R3: deferred_and_10_working_days")
    #     # print("validation_result;", validation_result)
    #     error_counter += 1
    #     row.update({"no_of_errors": error_counter})
    if biz_benefits == "Not Available":
        validation_rs.append("Violated_R4: invalid_missing_biz_benefits")
        # print("validation_result;", validation_result)
        error_counter += 1
    if biz_division == "Not Available":
        validation_rs.append("Violated_R5: invalid_missing_biz_division")
        # print("validation_result;", validation_result)
        error_counter += 1
    if biz_priority == "Not Available":
        validation_rs.append("Violated_R6: invalid_missing_biz_priority")
        # print("validation_result;", validation_result)
        error_counter += 1
    if bizexpect_timeline == "Not Available":
        validation_rs.append("Violated_R7: invalid_missing_bizexpect_timeline")
        # print("validation_result;", validation_result)
        error_counter += 1
    if error_counter == 0:
        validation_rs.append("Cleaned")
    row.update({"validation_result": ";".join(validation_rs)})
    row.update({"no_of_errors": error_counter})
    return row


def deliquency_row_add(row):
    row = age_since_approval_date_get(
        row)
    row = estimated_efforts_gen(row)
    row = start_date_gen(row)
    row = suggested_end_date_gen(
        row)
    row = bomc_delinquency_date_gen(row)
    row = ops_risk_delinquency_gen(row)
    return row


def review_row_add(row):
    row = age_since_approval_date_get(
        row)
    row = estimated_efforts_gen(row)
    row = start_date_gen(row)
    row = suggested_end_date_gen(
        row)
    row = bomc_delinquency_date_gen(row)
    row = ops_risk_delinquency_gen(row)
    row = completion_review_gen(row)
    row = efforts_estimation_review_gen(row)
    return row


def completion_review_gen(row):
    planned_end_date = row["suggested_end_date"]
    # actual_end_date = row["resolutiondate"]
    actual_end_date = datetime.datetime.strptime(
        row["resolutiondate"].rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')
    remarks = completion_review(datetime.datetime.strptime(
        planned_end_date, '%Y-%m-%d'), datetime.datetime.strptime(actual_end_date.strftime('%Y-%m-%d'), '%Y-%m-%d'))
    row["result"] = remarks.get("remarks")
    # row["diff"] = remarks.get("diff")
    return row


def efforts_estimation_review_gen(row):
    planned_start_date = row["suggested_start_date"]
    planned_end_date = row["suggested_end_date"]
    estimated_efforts = row["estimated_efforts"]
    # actual_end_date = row["resolutiondate"]
    # actual_end_date = datetime.datetime.strptime(
    #     row["resolutiondate"].rsplit("+", 1)[0], '%Y-%m-%dT%H:%M:%S.%f')
    remarks = estimation_review(datetime.datetime.strptime(
        planned_start_date, '%Y-%m-%d'), datetime.datetime.strptime(planned_end_date, '%Y-%m-%d'), float(estimated_efforts))
    row["efforts_review"] = remarks.get("remarks")
    return row


def ops_risk_delinquency_gen(row):
    age = row["age_till_cutoff_time"]
    status = row["biz_status"]
    approval_status = row["bom_decision"]
    row.update({"deliquency_90days": deliquency_90days_check(
        status, approval_status, age)})
    return row


def bomc_delinquency_date_gen(row):
    status = row["biz_status"]
    approval_status = row["bom_decision"]
    end_date = row["end_date"]
    suggested_end_date = row["suggested_start_date"]
    current_date = datetime.datetime.now().date()
    estimated_efforts = row["estimated_efforts"]
    if end_date != "Not Available":
        delinquency_date = biz_days_calculate(
            datetime.datetime.strptime(suggested_end_date, '%Y-%m-%d'), (float(estimated_efforts)/2))["suggested_end_date"]
    else:
        delinquency_date = biz_days_calculate(
            datetime.datetime.strptime(suggested_end_date, '%Y-%m-%d'), (float(estimated_efforts)/2))["suggested_end_date"]
    diff_days = (
        current_date - datetime.datetime.strptime(delinquency_date, '%Y-%m-%d').date()).days
    row.update({"deliquency_bomc": deliquency_bomc_check(
        status, approval_status, estimated_efforts, diff_days)})
    return row


def suggested_end_date_gen(row):
    estimated_efforts = row["estimated_efforts"]
    end_date = row["end_date"]
    suggested_start_date = row["suggested_start_date"]
    if end_date != "Not Available":
        row.update({"suggested_end_date": end_date})
        suggested_end_date = end_date
    else:
        suggested_end_date = biz_days_calculate(
            datetime.datetime.strptime(suggested_start_date, '%Y-%m-%d'), float(estimated_efforts))["suggested_end_date"]
        row.update({"suggested_end_date": suggested_end_date})
    return row


def start_date_gen(row):
    bomc_approval_date = None
    start_date = row["start_date"]
    if row["bom_approval_date"] != "Not Available":
        bomc_approval_date = row["bom_approval_date"]
    else:
        bomc_approval_date = row["created"]
    if start_date != "Not Available":
        row.update({"suggested_start_date": start_date})
        suggested_start_date = start_date
    else:
        suggested_start_date = biz_days_calculate(
            datetime.datetime.strptime(bomc_approval_date, '%Y-%m-%d'), float("1.0"))["suggested_start_date"]
        row.update({"suggested_start_date": suggested_start_date})
    return row


def estimated_efforts_gen(row):
    estimated_efforts = row["estimated_efforts"]
    if estimated_efforts == "Not Available":
        estimated_efforts = 12.0
        row.update({"estimated_efforts": estimated_efforts})
    return row


def age_since_approval_date_get(row):
    age = row["age_till_cutoff_time"]
    current_date = datetime.datetime.now().date()
    if row["bom_approval_date"] != "Not Available":
        bomc_approval_date = row["bom_approval_date"]
    else:
        bomc_approval_date = row["created"]
    if row["bom_approval_date"] != "Not Available":
        age_since_approval_date = (
            current_date - datetime.datetime.strptime(bomc_approval_date, '%Y-%m-%d').date()).days
        row.update({"age_since_approval_date": age_since_approval_date})
    else:
        age_since_approval_date = age
        row.update({"age_since_approval_date": age_since_approval_date})
    return row


def approval_date_get(row):
    if row["bom_approval_date"] != "Not Available":
        bomc_approval_date = row["bom_approval_date"]
    else:
        bomc_approval_date = row["created"]
    return bomc_approval_date


def deliquency_90days_check(status, approval_status, age):
    # print(status, approval_status, age)
    # print({
    #     'biz_status': status, 'age_till_cutoff_time': int(age), 'bom_decision': approval_status
    # })
    rule = rule_engine.Rule(
        'biz_status == "Open" and age_till_cutoff_time >= 90 and bom_decision in ["Approved","Approved by Department"]'
    )
    rul_rs = rule.matches({
        'biz_status': status, 'age_till_cutoff_time': int(age), 'bom_decision': approval_status
    })
    if rul_rs == True:
        return 1
    else:
        return 0


def deliquency_bomc_check(status, approval_status, efforts, diff_days):
    # print(status, approval_status, age)
    # print({
    #     'biz_status': status, 'age_till_cutoff_time': int(age), 'bom_decision': approval_status
    # })
    rule = rule_engine.Rule(
        'biz_status == "Open" and diff_days > 0 and bom_decision in ["Approved","Approved by Department"]'
    )
    rul_rs = rule.matches({
        'biz_status': status, 'diff_days': float(diff_days), 'efforts': float(efforts), 'bom_decision': approval_status
    })
    if rul_rs == True:
        return 1
    else:
        return 0


def add_column_in_csv_2(input_file, output_file, transform_row, tansform_column_names):
    """ Append a column in existing csv using csv.reader / csv.writer classes"""
    # Open the input_file in read mode and output_file in write mode
    with open(input_file, 'r') as read_obj, open(output_file, 'w', newline='') as write_obj:
        # Create a DictReader object from the input file object
        dict_reader = DictReader(read_obj)
        # Get a list of column names from the csv
        field_names = dict_reader.fieldnames
        # Call the callback function to modify column name list
        tansform_column_names(field_names)
        # Create a DictWriter object from the output file object by passing column / field names
        dict_writer = DictWriter(write_obj, field_names)
        # Write the column names in output csv file
        dict_writer.writeheader()
        # Read each row of the input csv file as dictionary
        for row in dict_reader:
            # Modify the dictionary / row by passing it to the transform function (the callback)
            transform_row(row, dict_reader.line_num)
            # Write the updated dictionary or row to the output file
            dict_writer.writerow(row)


def check_csv_empty(filename):
    # print("filename", filename)
    # print("size", os.stat(filename).st_size)
    if int(os.stat(filename).st_size) > 0:
        return False
    else:
        return True

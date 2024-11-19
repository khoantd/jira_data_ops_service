from common.json_util import create_json_file
import boto3
import uuid

client = boto3.client('quicksight')


def QS_ACCT_INFO_EXPORT():
    response = client.describe_account_settings(
        AwsAccountId='103629660136'
    )
    rs = create_json_file(response, 'samples/QSAccount_Info.json')
    return rs


def QS_DATASETS_LIST():
    ls = []
    paginator = client.get_paginator('list_data_sets')
    response_iterator = paginator.paginate(
        AwsAccountId='103629660136'
    )
    c = 0
    for i in response_iterator:
        data_ls = i["DataSetSummaries"]
        for j in data_ls:
            ls.append({
                "ID": c+1,
                "Name": j["Name"],
                "DataSetId": j["DataSetId"],
                "ImportMode": j["ImportMode"]
            })
            c = c+1
    create_json_file({
        "AwsAccountId": '103629660136',
        "QUickSightDataSetList": ls
    }, f'samples/QS_Datasets_List.json')

    return "success"


def QS_INGESTIONS_OF_DATASET_LIST(datasetid):
    # data_ls = None
    response = client.list_ingestions(
        DataSetId=datasetid,
        AwsAccountId='103629660136'
    )
    # rs = create_file(
    #     response, f'sample/{datasetid}.json')
    return response


def QS_DASHBOARDS_LIST():
    ls = []
    response = client.list_dashboards(
        AwsAccountId='103629660136'
    )
    # for i in response:
    data_ls = response["DashboardSummaryList"]
    c = 0
    for j in data_ls:
        ls.append({
            "ID": c+1,
            "Name": j["Name"],
            "DashboardId": j["DashboardId"],
            "PublishedVersionNumber": j["PublishedVersionNumber"]
        })
        c = c+1
    rs = create_json_file({
        "AwsAccountId": '103629660136',
        "QUickSightDashboardsList": ls
    }, f'samples/QS_Dashboards_List.json')
    return rs


def QS_INGESTION_CREATE(datasetid, mode='FULL_REFRESH'):
    response = client.create_ingestion(
        DataSetId=datasetid,
        IngestionId=str(uuid.uuid1()),
        AwsAccountId='103629660136',
        IngestionType=mode
    )
    # return response
    return {
        "IngestionId": response['IngestionId'],
        "IngestionStatus": response['IngestionStatus'],
        "RequestId": response['RequestId']
    }


def QS_INGESTION_QUERY(datasetid, requestid):
    response = client.create_ingestion(
        DataSetId=datasetid,
        IngestionId=requestid
    )
    return response

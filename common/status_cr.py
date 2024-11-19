# def change_request_type(argument):
#     switcher = {
#         "Code Change":
#         {
#             "customfield_13805": {
#                 "self": "https://fecredit.atlassian.net/rest/api/2/customFieldOption/17389",
#                 "value": "Code Change",
#                 "id": "17389"
#             }
#         },
#         "Code Change – New feature":
#         {
#             "customfield_13805": {
#                 "self": "https://fecredit.atlassian.net/rest/api/2/customFieldOption/17390",
#                 "value": "Code Change – New feature",
#                 "id": "17390"
#             }
#         },
#         "Code Change – Enhance existing feature":
#         {
#             "customfield_13805": {
#                 "self": "https://fecredit.atlassian.net/rest/api/2/customFieldOption/17391",
#                 "value": "Code Change – Enhance existing feature",
#                 "id": "17391"
#             }
#         },
#         "Parameter Change":
#         {
#             "customfield_13805": {
#                 "self": "https://fecredit.atlassian.net/rest/api/2/customFieldOption/17392",
#                 "value": "Parameter Change",
#                 "id": "17392"
#             }
#         },
#         "Parameter Change – UI Parameter Change Only":
#         {
#             "customfield_13805": {
#                 "self": "https://fecredit.atlassian.net/rest/api/2/customFieldOption/17393",
#                 "value": "Parameter Change – UI Parameter Change Only",
#                 "id": "17393"
#             }
#         },
#         "Parameter Change – Non-UI Parameter Change Only":
#         {
#             "customfield_13805": {
#                 "self": "https://fecredit.atlassian.net/rest/api/2/customFieldOption/17394",
#                 "value": "Parameter Change– Non-UI Parameter Change Only",
#                 "id": "17394"
#             }

#         }
#     }
#     return switcher.get(argument, "nothing")


def biz_and_jira_mapped_status(argument):
    switcher = {
        "New": "Open",
        "NEW": "Open",
        "0. New": "Open",
        "5.1 Test Failed": "Open",
        "Open": "Open",
        "1.1 Analyzing": "Open",
        "1.2 Review BRD": "Open",
        "ANALYSING": "Open",
        "Analyzing": "Open",
        "BRD Reviewing": "Open",
        "BRD REVIEWING": "Open",
        "CR Assigned": "Open",
        "Estimation Approval": "Open",
        "2.1 Estimation approval": "Open",
        "REQ Clarification": "Open",
        "REQ CLARIFICATION": "Open",
        "Technical Design": "Open",
        "Technical Solution": "Open",
        "1.3 Technical Solution": "Open",
        "Backlog": "Open",
        "CR Timeline": "Open",
        "Pega Planning": "Open",
        "PRIORITISED": "Open",
        "To Develop": "Open",
        "To Do": "Open",
        "3.1 In Development": "Open",
        "2.2 To Dev": "Open",
        "3.2 SIT Testing": "Open",
        "CR Development": "Open",
        "In Development": "Open",
        "In Progress": "Open",
        "REQUEST TO SIT": "Open",
        "Request to UAT": "Open",
        "SIT DONE": "Open",
        "SIT Released": "Open",
        "SIT Testing": "Open",
        "4. UAT Released": "Open",
        "UAT": "Open",
        "UAT Testing": "Open",
        "UAT Done": "Open",
        "5.2 UAT Done": "Open",
        "5. Done": "Closed",
        "6. Request to PROD": "Closed",
        "8. PROD Monitoring": "Closed",
        "3.3 SIT Done": "Open",
        "Closed": "Closed",
        "Closed / Done": "Closed",
        "Closed / Rejected": "Closed",
        "CR Confirmed": "Closed",
        "CR Deploying": "Closed",
        "Deploy to PROD": "Closed",
        "Done": "Closed",
        "PRO MONITORING": "Closed",
        "PROD Monitoring": "Closed",
        "PROD RELEASE APPROVED": "Closed",
        "Request to PROD": "Closed",
        "UAT DONE": "Closed",
        "UAT Released": "Closed",
        "CANCEL": "Closed",
        "Rejected": "Closed",
        "9. On Hold": "Closed",
        "On hold": "Closed",
        "On Hold": "Closed",
        "7. Store Build Approval": "Open",
        "Code Reviewing": "Open",
        "PRO DEPLOYING": "Open",
        "TECHNICAL SOLUTION": "Open",
        "PROD MONITORING": "Closed",
        "Confirmed UAT": "Open",
        "DONE": "Closed",
        "CLOSED": "Closed",
        "Rolled back": "Open"
    }
    return switcher.get(argument, "nothing")


def age_greater_than_90_days_category(argument):
    # print("age: ", argument)
    if argument >= 90:
        return 1
    else:
        return 0


def age_greater_than_30_days_category(argument):
    # print("age: ", argument)
    if argument >= 30 and argument < 90:
        return 1
    else:
        return 0


def age_less_than_30_days_category(argument):
    # print("age: ", argument)
    if argument < 30:
        return 1
    else:
        return 0


def status_details_and_jira_mapped_status(argument):
    switcher = {
        "Registered": "0. New",
        "In Review": "1. In Review",
        "CANCELED": "7. Canceled",
        "Rejected": "8. Rejected",
        "DEPLOYED IN PROD": "10. Deployed",
        "In Deployment": "9. In progress of Deployment",
        "Waiting for Approval": "3. Waiting for Approval",
        "In Security Review": "2. In Security Review",
        "Waiting for CAB Approval": "4. Waiting for CAB Approval",
        "Approved": "5. Approved",
        "Closed": "6. Done",
        "Rolled back": "9. In progress of Deployment"
    }
    return switcher.get(argument, "nothing")


def filtered_statuses_list_get(p_status):
    it_stage = []
    if p_status == 'completed':
        it_stage = ['5. Done', '6. Cancel or Rejected']
    if p_status == 'postapproval':
        it_stage = ['9. In progress of Deployment',
                    '10. Deployed', '5. Approved']

    return it_stage


def it_status_and_operation(argument):
    operation_name = {
        "0. New/Open": "initiation",
        "1. Analysis": "analysis",
        "2. In Queue for Dev": "in_queue_dev",
        "3. In Development": "in_dev",
        "4. UAT": "uat",
        "5. Done": "done",
        "6. Cancel or Rejected": "can_reject",
        "7. Hold": "hold"
    }
    return operation_name.get(argument, "Invalid IT status")


if __name__ == "__main__":
    argument = "Request to PROD"
    print(biz_and_jira_mapped_status(argument))
    print(status_details_and_jira_mapped_status(argument))

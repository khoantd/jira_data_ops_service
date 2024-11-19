import configparser
from datetime import datetime
import ssl
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import timezone
import pytz
from pytz import timezone, utc

SLACK_CFG_INI_PATH = 'cfg/cfg.ini'


def slack_cfg_load(slack_ini_file_path):
    config = configparser.ConfigParser()
    config.read(slack_ini_file_path)
    return config['SLACK']


def slack_token_get():
    slack_token = slack_cfg_load(SLACK_CFG_INI_PATH)['slack_token']
    return slack_token


def get_Slack_Client():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    # slack_token = os.environ["SLACK_BOT_TOKEN"]
    slack_token = slack_token_get()
    client = WebClient(token=slack_token, ssl=ssl_context)
    return client


def channel_message_sent(channel_name, blocks):
    rs = None
    client = get_Slack_Client()
    try:
        response = client.chat_postMessage(
            channel=channel_name,
            blocks=blocks
        )
        rs = response['ok']
        # print(response['ok'])
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        # str like 'invalid_auth', 'channel_not_found'
        assert e.response["error"]
        rs = False
    return rs


def slack_noti_send(function_name, status_of_process):
    local = datetime.now()
    print("Local:", local.strftime("%m/%d/%Y, %H:%M:%S"))
    tz_VN = pytz.timezone('Asia/Ho_Chi_Minh')
    datetime_VN = datetime.now(tz_VN)
    print("VN:", datetime_VN.strftime("%m/%d/%Y, %H:%M:%S"))
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f'Function *{function_name}* has just accomplished at *{datetime_VN.strftime("%m/%d/%Y, %H:%M:%S")}* with status *{status_of_process}*'
            }
        }
    ]
    print("Sent to Slack: ", channel_message_sent("#aws-lambda-noti", blocks))

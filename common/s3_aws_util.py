import boto3


def aws_s3_config_file_read(bucket, config_file):
    print()
    s3_boto = boto3.client('s3')
    obj = s3_boto.get_object(
        Bucket=bucket, Key=config_file)
    return obj['Body'].read().decode()


def config_file_read(location, config_file):
    if location == "S3":
        bucket = "rule-config-file"
        obj = aws_s3_config_file_read(bucket, config_file)
        return obj

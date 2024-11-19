import boto3
# pip install boto3

# Let's use Amazon S3
# s3 = boto3.resource("s3")

# Print out bucket names
# for bucket in s3.buckets.all():
#     print(bucket.name)


def push_file_to_s3(name, filename, bucket):
    # Create an S3 access object
    s3 = boto3.client("s3")
    # Pushing data to S3
    s3.upload_file(
        Filename=filename,
        Bucket=bucket,
        Key=name
    )


def download_file_from_s3(name, filename, bucket):
    s3 = boto3.client("s3")
    s3.download_file(Bucket=bucket, Key=name,
                     Filename=filename)
# s3.download_file(
#     Bucket="sample-bucket-1801", Key="train.csv", Filename="data/downloaded_from_s3.csv"
# )

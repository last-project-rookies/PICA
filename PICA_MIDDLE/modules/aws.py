import boto3
from botocore.client import Config
import json


class AwsQuery:
    def __init__(self):
        with open("key.json") as f:
            keys = json.load(f)
        self.S3 = boto3.resource(
            "s3",
            aws_access_key_id=keys["ACCESS_KEY_ID"],
            aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
            config=Config(signature_version="s3v4"),
            region_name="ap-northeast-2",
        )
        # self.SQS = boto3.client(
        #     "sqs",
        #     aws_access_key_id=keys["ACCESS_KEY_ID"],
        #     aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
        #     config=Config(signature_version="s3v4"),
        #     region_name="ap-northeast-2",
        # )
        self.BUCKET_NAME = "google-extension2"
        self.CLOUD_FLONT_CDN = "https://d2frc9lzfoaix3.cloudfront.net"

    async def s3_upload(self, userID, data):
        self.S3.Bucket(self.BUCKET_NAME).put_object(
            Key=f"{userID}/log_summary/yesterday.txt",
            Body=data,
        )

    async def s3_delete(self, userID, nickname, filename):
        self.S3.Object(self.BUCKET_NAME, f"{userID}/{nickname}/{filename}").delete()


if __name__ == "__main__":
    aws = AwsQuery()
    print(aws.S3)
    print(aws.BUCKET_NAME)
    print(aws.CLOUD_FLONT_CDN)

import boto3
from botocore.client import Config
import json
# 비동기 처리
import asyncio
from functools import wraps

# 스레드 처리 세팅
def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped


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
        self.SQS = boto3.client(
            "sqs",
            aws_access_key_id=keys["ACCESS_KEY_ID"],
            aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
            config=Config(signature_version="s3v4"),
            region_name="ap-northeast-2",
        )
        self.BUCKET_NAME = "pica-s3"
        self.CLOUD_FLONT_CDN = "https://d73fsaiivzjg2.cloudfront.net"
        self.AGENT_QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/434692986520/emtionQueue"
    
    def s3_log_upload(self, userID, data):
        self.S3.Bucket(self.BUCKET_NAME).put_object(
            Key=f"{userID}/log_summary/yesterday.txt",
            Body=data,
        )
    @async_action
    async def s3_delete(self, userID, nickname, filename):
        bucket = self.S3.Bucket(self.BUCKET_NAME)
        bucket.objects.filter(Prefix=f"{userID}/").delete()
        
    @async_action
    async def sqs_send(self, id, voice):
        result =  self.SQS.send_message(
            QueueUrl    = self.AGENT_QUEUE_URL,
            MessageBody = json.dumps({
                "id": str(id),
                "text": voice
                })
            )


if __name__ == "__main__":
    aws = AwsQuery()
    print(aws.S3)
    print(aws.BUCKET_NAME)
    print(aws.CLOUD_FLONT_CDN)

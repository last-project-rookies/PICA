import boto3
from botocore.client import Config
import json

# 비동기 처리
import asyncio
from functools import wraps
import base64


# 스레드 처리 세팅
def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapped


# aws 관련 함수 정의 (동기/비동기)
class AwsQuery:
    # 변수 초기화
    def __init__(self):
        with open("key.json") as f:
            keys = json.load(f)
        self.S3 = boto3.resource(
            "s3",
            aws_access_key_id=keys["ACCESS_KEY_ID"],
            aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
            config=Config(signature_version="s3v4"),
            region_name=keys["REGION"],
        )
        self.SQS = boto3.client(
            "sqs",
            aws_access_key_id=keys["ACCESS_KEY_ID"],
            aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
            config=Config(signature_version="s3v4"),
            region_name=keys["REGION"],
        )
        # 버킷
        self.BUCKET_NAME = "pica-s3"
        # CloudFlont CDN url
        self.CLOUD_FLONT_CDN = "https://d73fsaiivzjg2.cloudfront.net"
        # SQS queue url
        self.AGENT_QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/434692986520/emtionQueue"

    # S3에 요약본 업로드 함수
    def s3_log_upload(self, userID, data):
        """
        -arg
            - userID : `str` = 유저명
            - data : `str` = 요약본
        """
        self.S3.Bucket(self.BUCKET_NAME).put_object(
            Key=f"{userID}/log_summary/yesterday.txt",
            Body=data,
        )

    @async_action
    # S3에 요약본 업로드 함수
    async def s3_img_upload(self, userID, nickname, data):
        """
        -arg
            - userID : `str` = 유저명
            - data : `str` = 요약본
        """
        self.S3.Bucket(self.BUCKET_NAME).put_object(
            Key=f"{userID}/{nickname}/fun.jpg", Body=base64.b64decode(data)
        )

    def upload_base_64_to_s3(self, s3_file_name, base_64_str):
        aws.S3.Object(aws.BUCKET_NAME, s3_file_name).put(Body=base64.b64decode(base_64_str))
        return (aws.BUCKET_NAME, s3_file_name)

    # S3 객체 삭제
    @async_action
    async def s3_delete(self, userID, nickname):
        """
        - descript : 현재는 해당 사용자의 모든 정보 삭제 -> 나중에는 캐릭터의 객체만 삭제
        - arg
            - userID : `str` = 유저명
            - nickname : `str` = 캐릭터 이름
            - filename : `str` = 파일 이름
        """
        bucket = self.S3.Bucket(self.BUCKET_NAME)
        bucket.objects.filter(Prefix=f"{userID}/").delete()

    # SQS 메세지 보내기
    @async_action
    async def sqs_send(self, log_id, user_id, voice, time):
        """
        - descript : sqs queue 메시지 보내기
        - arg
            - log_id : `int` = log 테이블의 고유 번호
            - user_id : `int` = user 테이블의 고유 번호
            - voice : `str` = 사용자의 입력 메시지
            - time : `time` = 해당 메시지 날짜
        """
        result = self.SQS.send_message(
            QueueUrl=self.AGENT_QUEUE_URL,
            MessageBody=json.dumps(
                {
                    "log_id": str(log_id),
                    "user_id": str(user_id),
                    "text": voice,
                    "year": time.year,
                    "month": time.month,
                    "day": time.day,
                    "hour": time.hour,
                    "minute": time.minute,
                    "second": time.second,
                }
            ),
        )


if __name__ == "__main__":
    aws = AwsQuery()
    print(aws.BUCKET_NAME)
    print(aws.CLOUD_FLONT_CDN)
    aws.s3_img_upload(
        "hello",
        "hello",
    )

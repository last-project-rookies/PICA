import requests
import asyncio
import json

# "source_url": f"https://google-extension2.s3.ap-northeast-2.amazonaws.com/upload/{key}"
TOKEN = "Basic Y21welpHNWhhMlp0ZW1nMk1VQm5iV0ZwYkM1amIyMDpTeG5OYUNnbkpKYkl5WGRsNTRpRlQ="


async def create_did(key, img_url):
    """
    - descript = d-id api 호출 및 텍스트와 이미지 삽입해서 영상 생성
    - arg
        - key : `string` = bing 의 대답 문자
        - img_url : `string` = 스테이블 디퓨젼이 생성한 이미지의 url 문자
    - return
        - response.text : `string` = d-id 요청 결과
    """
    url = "https://api.d-id.com/talks"

    payload = {
        "script": {
            "type": "text",
            "provider": {"type": "microsoft", "voice_id": "ko-KR-SeoHyeonNeural"},
            "ssml": "false",
            "input": f"{key}",
        },
        "config": {
            "fluent": "false",
            "pad_audio": "0.0",
            "result_format": "mp4",
            "stitch": True,
            "sharpen": True,
            "align_expand_factor": 0,
        },
        "source_url": img_url,
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": TOKEN,
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.text


async def get_did(talk_id):
    """
    - descript = 고유번호를 이용하여 d-id에 생성된 영상 요청
    - arg
        - talk_id : `string` = d-id에 생성된 고유 번호
    - return
        - response.text : `string` = d-id 요청 결과
    """
    url = f"https://api.d-id.com/talks/{talk_id}"

    headers = {
        "accept": "application/json",
        "authorization": TOKEN,
    }

    response = requests.get(url, headers=headers)

    return response.text


# D-ID 영상 생성
async def make_d_id(msg, URL):
    """
    - descript = d-id 실행
    - arg
        - msg : `string` = bing 대답 메시지
        - URL : `string` = 스테이블 디퓨젼 이미지 주소
    - return
        - result_url : `string` = d-id 영상 url
    """
    result_url = None

    creation = json.loads(await create_did(msg, URL))
    if (
        creation.get("kind") == "InsufficientCreditsError"
        or creation.get("kind") == "InternalServerError"
        or creation.get("kind") == "NotFoundError"
    ):
        result_url = URL
        print("d-id error")
    else:
        while True:
            result = json.loads(await get_did(creation.get("id")))
            result_url = result.get("result_url")
            if result_url:
                break
    print("생성~")
    return result_url


if __name__ == "__main__":
    img_url = "https://pica-s3.s3.ap-northeast-2.amazonaws.com/%EC%95%84%EC%9D%B4%EC%9C%A0.jpg"
    tmp = asyncio.run(make_d_id("안녕하세요", img_url))
    print(tmp)

from flask import Flask, jsonify, request
from modules.did import make_d_id

# from modules.chat import being_call
from modules.gpt.chat import gpt_call, setting
from modules.gpt.summary import make_summary
from modules.gpt.emotion import chat_emotion
from modules.aws import AwsQuery
from modules.db import db_select_id, db_insert, db_delete, db_select_url, db_select_log
import asyncio
import requests
import json
import urllib.request
import os
import shutil

app = Flask(__name__)
app.config["SECRET_KEY"] = "PICA_MIDDLE"
aws = AwsQuery()


# 예시 요청 받기
@app.route("/example", methods=["GET", "POST"])
def example():
    tmp = request.get_json()
    print(tmp, type(tmp))
    print("hiih")
    data = {"check": "hihi"}
    return jsonify(data)


# get_img 요청 처리
@app.route("/get_img", methods=["GET", "POST"])
def get_img():
    data = request.get_json()
    user_id = data.get("user_id")
    # db에서 cloudflont url 가져오기
    urls = db_select_url(db_select_id(user_id))
    return jsonify({"url": urls[1]})


# delete_img 요청 처리
@app.route("/delete_img", methods=["GET", "POST"])
def delete_img():
    data = request.get_json()
    # url 받아오기
    user_id = data.get("user_id")
    nickname = data.get("nickname")
    filename = data.get("filename")
    # aws s3 데이터 삭제
    asyncio.run(aws.s3_delete(user_id, nickname, filename))
    # db & session 삭제
    db_delete(db_select_id(user_id))

    return jsonify({"data": None})


# req_stable 요청 처리
@app.route("/req_stable", methods=["GET", "POST"])
def req_stable():
    # 데이터 받아오기
    data = request.get_json()
    b_img = data.get("b_img")
    user_id = data.get("user_id")
    nickname = data.get("nickname")
    url = None
    try:
        # # # 2. 스테이블 디퓨전 서버에 POST 전송
        # res = requests.post(
        #     "https://96694122-1ac1-4eb9.gradio.live/base64file",
        #     json.dumps({"base64_file": b_img, "user_id": user_id}),
        # )
        # print(res.status_code)

        # res_text = res.json()
        # img_name = json.loads(res_text).get("img_name")

        # # 3. url 생성
        # url = aws.CLOUD_FLONT_CDN + f"/{user_id}/{img_name}"

        # 임시 url
        url = (
            aws.CLOUD_FLONT_CDN
            + f"/{user_id}/{nickname}/059f665f-a414-4d7f-adea-d0c8665bb0e6_fun.jpg"
        )

        # 4. db-user, url 테이블 삽입
        db_insert("user", user_id)
        id_value = db_select_id(user_id)
        db_insert("url", f"'{url}', '{url}', '{url}', {id_value}")
        print(url)

    except Exception as e:
        print("request error : ", e)

    # 웹에 전달
    return jsonify({"url": url})


# send_message 요청 처리
@app.route("/send_message", methods=["GET", "POST"])
def send_message():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        voice = data.get("voice")

        # gpt
        # 1. bing
        # being_msg = asyncio.run(being_call(voice))

        # 2. lang_chain
        # setting -> 유저 정보 -> 로그인 할떄 세팅
        conversation, memory_vectorstore, static_vectorstore = setting()
        chat = asyncio.run(gpt_call(voice, conversation, memory_vectorstore, static_vectorstore))

        # 3. emotion 분석
        user_emotion = asyncio.run(chat_emotion("user", voice))
        max_value = max(user_emotion.get("emotion").values())
        # q_status : 사용자 감정 상태
        for idx, (_, value) in enumerate(user_emotion.get("emotion").items()):
            if value == max_value:
                q_status = idx + 1
                break

        gpt_emotion = asyncio.run(chat_emotion("gpt", chat))
        max_value = max(gpt_emotion.get("emotion").values())
        # a_status : gpt 감정 상태
        for idx, (_, value) in enumerate(gpt_emotion.get("emotion").items()):
            if value == max_value:
                a_status = idx + 1
                break

        # 감정 결과 fun,sad,angry -> urls[1], urls[2], urls[3]
        urls = db_select_url(db_select_id(user_id))

        # d-id
        # video_url = asyncio.run(make_d_id(being_msg, urls[a_status]))
        video_url = ""

        # 각종 log db 저장
        id_value = db_select_id(user_id)
        db_insert("log", f"'{voice}', '{chat}', {a_status}, {q_status}, '{video_url}', {id_value}")
    except asyncio.TimeoutError:
        print("except error")

    return jsonify({"msg": chat, "video_url": video_url})


async def log_summary_upload(user_id):
    chat_log = db_select_log()
    texts = ""
    for _, (_, voice, chat, _, _, _, _) in enumerate(chat_log):
        texts += "voice : " + voice + "chat : " + chat
    chat_summary = await make_summary(texts)
    await aws.s3_upload(user_id, data=chat_summary)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    data = request.get_json()
    user_id = data.get("user_id")
    asyncio.run(log_summary_upload(user_id))
    if os.path.exists(f"user_id"):
        shutil.rmtree(f"{user_id}")
    return jsonify({})


def read_summary():
    with urllib.request.urlopen(
        "https://d2frc9lzfoaix3.cloudfront.net/userid/log_summary/yesterday.txt"
    ) as response:
        txt = response.read().decode("utf-8")
    print(txt)


if __name__ == "__main__":
    app.run(port=3000, debug=True)
    # read_summary()
# waitress-serve --port=3000 --channel-timeout=30 app:app

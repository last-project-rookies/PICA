from flask import Flask, jsonify, request
from modules.did import make_d_id
from modules.chat import being_call
from modules.aws import AwsQuery
from modules.db import db_select_id, db_insert, db_delete, db_select_url
import asyncio
import requests
import json

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
    user_id, name = data.get("user_id"), data.get("name")
    # aws s3 데이터 삭제
    asyncio.run(aws.s3_delete(user_id, name))
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
    url = None
    try:
        # # 2. 스테이블 디퓨전 서버에 POST 전송
        res = requests.post(
            "https://8623c46562b88b0770.gradio.live/base64file",
            json.dumps({"base64_file": b_img, "user_id": user_id}),
        )
        print(res.status_code)

        res_text = res.json()
        img_name = json.loads(res_text).get("img_name")

        # 3. url 생성
        url = aws.CLOUD_FLONT_CDN + f"/{user_id}/{img_name}"

        # 임시 url
        # url = aws.CLOUD_FLONT_CDN + "/hi/iu.jpg"

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
        being_msg = asyncio.run(being_call(voice))

        # 감정 결과 fun,sad,angry -> urls[1], urls[2], urls[3]
        urls = db_select_url(db_select_id(user_id))

        # d-id
        video_url = asyncio.run(make_d_id(being_msg, urls[1]))

        # 각종 log db 저장
        # a_status : 감정 상태
        a_status = 1
        id_value = db_select_id(user_id)
        db_insert("log", f"'{voice}', '{being_msg}', {a_status}, '{video_url}', {id_value}")
    except asyncio.TimeoutError:
        print("except error")

    return jsonify({"video_url": video_url})


if __name__ == "__main__":
    app.run(port=3000, debug=True)
# waitress-serve --port=3000 --channel-timeout=30 app:app

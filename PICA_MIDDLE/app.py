# 모듈
from modules.did import make_d_id
from modules.gpt.chat import gpt_call, setting
from modules.gpt.summary import make_summary
from modules.gpt.emotion import chat_emotion
from modules.aws import AwsQuery

from modules.db import (
    db_select_id,
    db_insert,
    db_delete,
    db_select_url,
    db_select_log,
    db_select_chatid,
    db_select_mbti,
    db_select_chat_log,
    pieChart_data,
    total_chat_count_data,
    generate_chart_data,
    db_select_user,
)



# 비동기 처리
import asyncio
import threading
from functools import wraps

# 각종 라이브러리
from flask import Flask, jsonify, request
import requests
import json
import urllib.request
import os
import shutil
from datetime import datetime
from pytz import timezone


# 스레드 처리 세팅
def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapped


app = Flask(__name__)
app.config["SECRET_KEY"] = "PICA_MIDDLE"
aws = AwsQuery()
conversation, memory_vectorstore, static_vectorstore = None, None, None

face_compile = {"dog": 0, "cat": 1}
sex_compile = {"man": 0, "girl": 1}


# delete_img 요청 처리
@app.route("/delete_img", methods=["GET", "POST"])
def delete_img():
    data = request.get_json()
    # url 받아오기
    user_id = data.get("user_id")
    nickname = data.get("nickname")
    filename = data.get("filename")
    # aws s3 데이터 삭제
    th_aws_delete = threading.Thread(target=aws.s3_delete, args=(user_id, nickname))
    th_aws_delete.start()
    th_aws_delete.join()
    # db & session 삭제
    id_value = db_select_id(user_id)
    th_delete = threading.Thread(target=db_delete, args=(id_value,))
    th_delete.start()
    th_delete.join()

    return jsonify({"data": None})


# req_stable 요청 처리
@app.route("/req_stable", methods=["GET", "POST"])
def req_stable():
    # 데이터 받아오기
    data = request.get_json()
    b_img = data.get("b_img")
    user_id = data.get("user_id")
    nickname = data.get("nickname")
    sex = data.get("sex")
    face = data.get("face")
    mbti = data.get("mbti")

    # 기본 이미지
    base_data = None

    try:
        # 2. 스테이블 디퓨전 서버에 POST 전송 "face_id":face,
        res = requests.post(
            "http://54.248.40.115:8080/img2img",
            json.dumps({"base64_file": b_img, "user_id": user_id + f"/{nickname}", "sex": sex}),
        )
        print(res.status_code)

        res_text = res.json()
        base_data = json.loads(res_text).get("base_data")

        # # 임시 url
        # fun_url = (
        #     aws.CLOUD_FLONT_CDN
        #     + f"/{user_id}/{nickname}/bacf6439-4e0d-4676-87a1-c650ce3e503b_fun.jpg"
        # )
        # sad_url = (
        #     aws.CLOUD_FLONT_CDN
        #     + f"/{user_id}/{nickname}/bacf6439-4e0d-4676-87a1-c650ce3e503b_fun.jpg"
        # )
        # angry_url = (
        #     aws.CLOUD_FLONT_CDN
        #     + f"/{user_id}/{nickname}/bacf6439-4e0d-4676-87a1-c650ce3e503b_fun.jpg"
        # )

        # 4. db- user 테이블 삽입
        th_user = threading.Thread(target=db_insert, args=("user", user_id))
        th_user.start()
        th_user.join()
        id_value = db_select_id(user_id)
        th_user = threading.Thread(
            target=db_insert,
            args=(
                "vir_character",
                f" '{mbti}', {face_compile[face]}, {sex_compile[sex]}, '{nickname}', {id_value}",
            ),
        )
        th_user.start()
        th_user.join()
        th_user = threading.Thread(target=db_insert, args=("accum_emotion", id_value))
        th_user.start()
        th_user.join()

    except Exception as e:
        print("request error : ", e)

    # 웹에 전달
    return jsonify({"base_data": base_data})


# re_req_stable 재요청 처리
@app.route("/re_req_stable", methods=["GET", "POST"])
def re_req_stable():
    base_data = None
    # 2. 스테이블 디퓨전 서버에 POST 전송
    try:
        res = requests.post("http://54.248.40.115:8080/reset2img")
        res_text = res.json()
        base_data = json.loads(res_text).get("base_data")
    except Exception as e:
        print("request error : ", e)

    return jsonify({"base_data": base_data})


# finish_req_stable 결정된 stable 이미지 업로드
@app.route("/finish_req_stable", methods=["GET", "POST"])
def finish_req_stable():
    print("!!!!!!!!!!!!! finish_req_stable")
    # 데이터 받아오기
    data = request.get_json()
    b_img = data.get("b_img")
    user_id = data.get("user_id")
    nickname = data.get("nickname")

    id_value = db_select_id(user_id)
    mbti = db_select_mbti(id_value)

    # aws s3 이미지 업로드
    th_aws_img_upload = threading.Thread(target=aws.s3_img_upload, args=(user_id, nickname, b_img))
    th_aws_img_upload.start()
    th_aws_img_upload.join()
    # db - url 테이블 삽입
    fun_url = aws.CLOUD_FLONT_CDN + f"/{user_id}/{nickname}/fun.jpg"
    sad_url = aws.CLOUD_FLONT_CDN + f"/{user_id}/{nickname}/sad.jpg"
    angry_url = aws.CLOUD_FLONT_CDN + f"/{user_id}/{nickname}/angry.jpg"
    print(fun_url)
    th_url = threading.Thread(
        target=db_insert, args=("url", f"'{fun_url}', '{sad_url}', '{angry_url}', {id_value}")
    )
    th_url.start()
    th_url.join()

    # 캐릭터 대화 세팅
    global conversation, memory_vectorstore, static_vectorstore
    conversation, memory_vectorstore, static_vectorstore = setting(
        user_get=user_id, name_get=nickname, mbti_get=mbti, age_get="22", user_id_get=user_id
    )
    return jsonify({})


# send_message 요청 처리
@app.route("/send_message", methods=["GET", "POST"])
def send_message():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        voice = data.get("voice")
        time = datetime.now(timezone("Asia/Seoul"))
        time_str = time.strftime("%Y-%m-%d %H:%M:%S")

        # 1. lang_chain
        # setting -> 유저 정보 -> 캐릭터 생성할 때 세팅
        global conversation, memory_vectorstore, static_vectorstore
        chat = asyncio.run(gpt_call(voice, conversation, memory_vectorstore, static_vectorstore))

        # 2. emotion 분석
        gpt_emotion = asyncio.run(chat_emotion("gpt", chat))
        max_value = max(gpt_emotion.get("emotion").values())
        # a_status : gpt 감정 상태
        for idx, (_, value) in enumerate(gpt_emotion.get("emotion").items()):
            if value == max_value:
                a_status = idx + 1
                break

        # 3. 감정 결과 fun,sad,angry -> urls[1], urls[2], urls[3]
        urls = db_select_url(db_select_id(user_id))

        # 4. d-id
        # video_url = asyncio.run(make_d_id(chat, urls[a_status]))
        video_url = ""

        # 5. 각종 log db 저장
        id_value = db_select_id(user_id)
        th_log = threading.Thread(
            target=db_insert,
            args=(
                "log",
                f"'{voice}', '{chat}', {a_status}, '{video_url}', {id_value}, '{time_str}'",
            ),
        )
        th_log.start()
        th_log.join()

        # 6. aws sqs msg
        chatid = db_select_chatid(id_value)
        th_sqs = threading.Thread(target=aws.sqs_send, args=(chatid, id_value, voice, time))
        th_sqs.start()
        th_sqs.join()

    except asyncio.TimeoutError:
        print("except error")

    return jsonify({"msg": chat, "video_url": video_url})


# 요약본 S3 업로드 (비동기처리)
@async_action
async def log_summary_upload(user_id):
    chat_log = db_select_log()
    texts = ""
    for _, (_, voice, chat, _, _, _, _) in enumerate(chat_log):
        texts += "voice : " + voice + "chat : " + chat
    chat_summary = await make_summary(texts)
    aws.s3_log_upload(user_id, data=chat_summary)


# 로그아웃 로직
@app.route("/logout", methods=["GET", "POST"])
def logout():
    data = request.get_json()
    user_id = data.get("user_id")
    # 스레드 처리
    th_upload = threading.Thread(target=log_summary_upload, args=(user_id,))
    th_upload.start()
    th_upload.join()
    if os.path.exists(f"user_id"):
        shutil.rmtree(f"{user_id}")

    return jsonify({})


@app.route("/user_table_request", methods=["GET", "POST"])
def user_table_request():
    result = db_select_user()
    data = dict()
    for idx, val in result:
        data[idx] = val
    return jsonify({"data": data})


# 파이차트 데이터
@app.route("/pie_chart_data", methods=["GET", "POST"])
def pie_chart_data():
    data = request.get_json()
    user_id = data.get("user_id")
    id_value = db_select_id(user_id)
    pie_data = pieChart_data(id_value)
    return jsonify({"data": pie_data})


# 전체 대화 개수
@app.route("/total_conversations", methods=["GET", "POST"])
def get_total_conversations():
    data = request.get_json()
    user_id = data.get("user_id")
    print(user_id)
    id_value = db_select_id(user_id)
    print(id_value)
    total_conversations = total_chat_count_data(id_value)
    return jsonify({"data": total_conversations})


# 선차트 데이터(감정별 데이터)
@app.route("/update_chart_data", methods=["GET", "POST"])
def update_chart_data():
    data = request.get_json()
    user_id = data.get("user_id")
    emotion = data.get("emotion")
    id_value = db_select_id(user_id)

    chart_data = generate_chart_data(emotion, id_value)

    return jsonify({"data": chart_data})


# 대화 로그
@app.route("/admin_chatlog", methods=["GET", "POST"])
def admin_chatlog():
    data = request.get_json()
    user_id = data.get("user_id")
    id_value = db_select_id(user_id)
    chat_log_db = db_select_chat_log(id_value)
    print(chat_log_db)
    return jsonify({"data": chat_log_db})


# user_id 불러오기
@app.route('/get_text', methods=['GET'])
def get_text():
    # 서버에서 가져올 텍스트를 이 부분에서 처리하고 가져오는 로직을 구현합니다.
    text = db_select_last_userID()

    return jsonify({'data':text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
    # read_summary()

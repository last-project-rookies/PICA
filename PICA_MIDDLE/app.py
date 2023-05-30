# 모듈
from modules.did import make_d_id
from modules.gpt.chat import gpt_call, setting
from modules.gpt.summary import make_summary
from modules.gpt.emotion import chat_emotion
from modules.aws import AwsQuery
from modules.db import db_select_id, db_insert, db_delete, db_select_url, db_select_log, db_select_chatid

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
    th_aws_delete = threading.Thread(target=aws.s3_delete, args=(user_id, nickname, filename))
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
    fun_url = None
    try:
        # 2. 스테이블 디퓨전 서버에 POST 전송
        # res = requests.post(
        #     "http://54.248.40.115:8080/img2img",
        #     json.dumps({"base64_file": b_img, "user_id": user_id + f"/{nickname}"}),
        # )
        # print(res.status_code)

        # res_text = res.json()
        # fun_img = json.loads(res_text).get("img_name")
        # sad_img = fun_img.replace('_fun','_sad')
        # angry_img = fun_img.replace('_fun', '_angry')
        # # 3. url 생성
        # fun_url = aws.CLOUD_FLONT_CDN + f"/{user_id}/{nickname}/{fun_img}"
        # sad_url = aws.CLOUD_FLONT_CDN + f"/{user_id}/{nickname}/{sad_img}"
        # angry_url = aws.CLOUD_FLONT_CDN + f"/{user_id}/{nickname}/{angry_img}"

        # 임시 url
        fun_url = (
            aws.CLOUD_FLONT_CDN
            + f"/{user_id}/{nickname}/fun.jpg"
        )
        sad_url = (
            aws.CLOUD_FLONT_CDN
            + f"/{user_id}/{nickname}/bacf6439-4e0d-4676-87a1-c650ce3e503b_fun.jpg"
        )        
        angry_url = (
            aws.CLOUD_FLONT_CDN
            + f"/{user_id}/{nickname}/bacf6439-4e0d-4676-87a1-c650ce3e503b_fun.jpg"
        )
        
        # 4. db- user, url 테이블 삽입
        print(fun_url)
        th_user = threading.Thread(target=db_insert,args=("user", user_id))
        th_user.start()
        th_user.join()
        id_value = db_select_id(user_id)
        th_user = threading.Thread(target=db_insert,args=("accum_emotion", id_value))
        th_user.start()
        th_user.join()
        th_url = threading.Thread(target=db_insert,args=("url", f"'{fun_url}', '{sad_url}', '{angry_url}', {id_value}"))
        th_url.start()
        th_url.join()
        
    except Exception as e:
        print("request error : ", e)

    # 웹에 전달
    return jsonify({"url": fun_url})


# send_message 요청 처리
@app.route("/send_message", methods=["GET", "POST"])
def send_message():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        voice = data.get("voice")
        time = datetime.now(timezone('Asia/Seoul'))
        time_str = time.strftime("%Y-%m-%d %H:%M:%S")

        # 1. lang_chain
        # setting -> 유저 정보 -> 로그인 할떄 세팅
        conversation, memory_vectorstore, static_vectorstore = setting(user_get="이건우", name_get="이루다", mbti_get="ISTJ", age_get="22", user_id_get=user_id)
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
        th_log = threading.Thread(target=db_insert, args=("log", f"'{voice}', '{chat}', {a_status}, '{video_url}', {id_value}, '{time_str}'"))
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

@async_action
async def log_summary_upload(user_id):
    chat_log = db_select_log()
    texts = ""
    for _, (_, voice, chat, _, _, _, _) in enumerate(chat_log):
        texts += "voice : " + voice + "chat : " + chat
    chat_summary = await make_summary(texts)
    aws.s3_log_upload(user_id, data=chat_summary)
    


@app.route("/logout", methods=["GET", "POST"])
def logout():
    data = request.get_json()
    user_id = data.get("user_id")
    # 스레드 처리
    th_upload = threading.Thread(target=log_summary_upload,args=(user_id,))
    th_upload.start()
    th_upload.join()
    if os.path.exists(f"user_id"):
        shutil.rmtree(f"{user_id}")
        
    return jsonify({})

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=3000, debug=True)
    # read_summary()
# waitress-serve --port=3000 --channel-timeout=30 app:app

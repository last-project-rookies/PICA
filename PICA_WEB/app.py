from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import asyncio
import requests
import time
import base64

app = Flask(__name__)
app.config["SECRET_KEY"] = "PICA_WEB"
app.config["JSON_AS_ASCII"] = False
# aws_addr = '13.125.120.92' 
aws_addr = 'pica-middle-1' 
stable_img = None

#################################################### 라우터 

# 홈 페이지(캐릭터 입력 & 관리자 페이지)
@app.route("/")
def home():
    return render_template("index.html")

# 캐릭터 정보 입력 페이지
@app.route("/input")
def input():
    return render_template("pages/input.html")

# 캐릭터 생성 페이지
@app.route("/make")
def make():
    global stable_img
    return render_template("pages/make.html", img=stable_img)

# chatbot 페이지
@app.route("/chatbot")
def chatbot():
    global stable_img
    
    try:
        # session 상태 확인
        if "user_id" not in session:
            flash("이미지를 생성하지 못했습니다. 다시 생성해 주세요")
            return redirect(url_for("input"))
        else:
            return render_template("pages/chatbot.html", img=stable_img)
    except Exception as e:
        flash("이미지가 삭제되었습니다. 새로운 캐릭터를 만들어주세요!")
        return redirect(url_for("input"))
    return render_template("pages/chatbot.html")

# 관리자 페이지
@app.route("/admin")
def admin():
    return render_template("pages/admin.html")

#################################################### 로직

# chatbot 페이지 로드직후 default 이미지 가져오기

# 유저 정보 및 이미지 삭제
@app.route("/delete_img", methods=["GET", "POST"])
def delete_img():
    # url 받아오기
    url = request.get_json().get("url")
    user_id, nickname, filename = url.split("/")[-3], url.split("/")[-2], url.split("/")[-1]
    data = {"user_id": user_id, "nickname": nickname, "filename": filename}

    # 요청
    try:
        res = requests.post(f"http://{aws_addr}:3000/delete_img", json=data)
    except Exception as e:
        print("delete_img error : ", e)

    # session 삭제
    session.pop("user_id", None)

    return jsonify({"data": None})


# 스테이블 디퓨전 이미지 생성
@app.route("/req_stable", methods=["GET", "POST"])
def req_stable():
    # 데이터 받아오기
    b_img = request.get_json()["b_img"]
    user_id = request.get_json()["userID"]
    nickname = request.get_json()["nickname"]
    sex = request.get_json()["sex"]
    face = request.get_json()["face"]
    mbti = request.get_json()["mbti"]
    
    session["nickname"] = nickname
    session["user_id"] = user_id
    
    data = {
        "b_img": b_img, 
        "user_id": user_id, 
        "nickname": nickname,
        "sex": sex,
        "face": face,
        "mbti": mbti
        }
    
    base_data = None
    # 요청
    try:
        res = requests.post(f"http://{aws_addr}:3000/req_stable", json=data)
        base_data = res.json().get("base_data") 
        global stable_img
        stable_img = base_data
        
    except requests.exceptions.ConnectionError as e:
        print("req_stable error : ", e)
        return redirect(url_for("input"))
    return jsonify({})

@app.route("/re_req_stable", methods=["GET", "POST"])
def re_req_stable():
    base_data = None
    # 재요청
    try:
        res = requests.post(f"http://{aws_addr}:3000/re_req_stable")
        base_data = res.json().get("base_data")
        global stable_img
        stable_img = base_data
    except requests.exceptions.ConnectionError as e:
        print("re_req_stable error : ", e)
        return redirect(url_for("make"))

    return jsonify({"b_img":base_data})

@app.route("/finish_req_stable", methods=["GET", "POST"])
def finish_req_stable():
    user_id = session["user_id"]
    nickname = session["nickname"]
    global stable_img
    data = {"user_id": user_id, "nickname":nickname, "b_img":stable_img}
    # 이미지 업로드 요청
    try:
        res = requests.post(f"http://{aws_addr}:3000/finish_req_stable", json=data)
        
    except requests.exceptions.ConnectionError as e:
        print("re_req_stable error : ", e)
        return redirect(url_for("make"))
    
    return jsonify({})

# voice 입력 후 bing(gpt) & d-id 처리
@app.route("/send_message", methods=["GET", "POST"])
def send_message():
    user_id = session["user_id"]
    nickname = session["nickname"]
    # voice
    voice = request.get_json()["inputdata"]
    data = {"voice": voice, "user_id": user_id}
    msg = None
    video_url = None
    # 요청
    try:
        res = requests.post(f"http://{aws_addr}:3000/send_message", json=data)
        video_url = res.json().get("video_url")
        msg = res.json().get("msg")
    except Exception as e:
        print("send_message error : ", e)
    return jsonify({"info": {"nickname": nickname, "answer": msg}, "video_url": video_url})

# 로그아웃
@app.route("/logout")
def logout():
    user_id = session["user_id"]
    data = {"user_id": user_id}
    # 요청
    try:
        res = requests.post(f"http://{aws_addr}:3000/logout", json=data)
    except Exception as e:
        print("logout error : ", e)
    
    return jsonify({})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3333, debug=True)
# waitress-serve --port=5000 --channel-timeout=300 app:app

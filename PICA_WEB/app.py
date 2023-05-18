from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import asyncio
import requests
import time

app = Flask(__name__)
app.config["SECRET_KEY"] = "PICA_WEB"


# 예시 페이지
@app.route("/example")
def example():
    res = requests.post("http://127.0.0.1:3000/example", json={"data": "post"})
    print(res)
    tmp = res.json().get("check")
    print(tmp, type(tmp))
    return render_template("example.html")


# chatbot 페이지 로드직후 default 이미지 가져오기
@app.route("/get_img")
def get_img():
    user_id = session["user_id"]
    data = {"user_id": user_id}
    # 요청
    try:
        res = requests.post("http://127.0.0.1:3000/get_img", json=data)
        url = res.json().get("url")
    except Exception as e:
        print("get_img error : ", e)
        return redirect(url_for("home"))

    return jsonify({"url": url})


# 유저 정보 및 이미지 삭제
@app.route("/delete_img", methods=["GET", "POST"])
def delete_img():
    # url 받아오기
    url = request.get_json().get("url")
    user_id, nickname, filename = url.split("/")[-3], url.split("/")[-2], url.split("/")[-1]
    data = {"user_id": user_id, "nickname": nickname, "filename": filename}

    # 요청
    try:
        res = requests.post("http://127.0.0.1:3000/delete_img", json=data)
    except Exception as e:
        print("delete_img error : ", e)

    # session 삭제
    session.pop("user_id", None)

    return jsonify({"data": None})


# 홈 페이지(회원가입 페이지)
@app.route("/")
def home():
    return render_template("index.html")


# chatbot 페이지
@app.route("/chatbot")
def chatbot():
    try:
        # session 상태 확인
        if "user_id" not in session:
            flash("이미지를 생성하지 못했습니다. 다시 생성해 주세요")
            return redirect(url_for("home"))
        else:
            return render_template("chatbot.html")
    except Exception as e:
        flash("이미지가 삭제되었습니다. 새로운 캐릭터를 만들어주세요!")
        return redirect(url_for("home"))


# 로딩 페이지
@app.route("/loading")
def loading():
    time.sleep(5)
    return render_template("loading.html")


# 스테이블 디퓨전 이미지 생성
@app.route("/req_stable", methods=["GET", "POST"])
def req_stable():
    # 데이터 받아오기
    b_img = request.get_json()["b_img"]
    user_id = request.get_json()["userID"]
    nickname = request.get_json()["nickname"]
    # password = request.get_json()["password"]

    session["user_id"] = user_id
    data = {"b_img": b_img, "user_id": user_id, "nickname": nickname}
    # 요청
    try:
        res = requests.post("http://127.0.0.1:3000/req_stable", json=data)
        url = res.json().get("url")
    except Exception as e:
        print("req_stable error : ", e)
        return redirect(url_for("home"))

    return jsonify({"url": url})


# voice 입력 후 bing(gpt) & d-id 처리
@app.route("/send_message", methods=["GET", "POST"])
def send_message():
    user_id = session["user_id"]
    # voice
    voice = request.get_json()["inputdata"]
    data = {"voice": voice, "user_id": user_id}

    # 요청
    try:
        res = requests.post("http://127.0.0.1:3000/send_message", json=data)
        video_url = res.json().get("video_url")
    except Exception as e:
        print("send_message error : ", e)
    return jsonify({"video_url": video_url})


@app.route("/logout")
def logout():
    user_id = session["user_id"]
    data = {"user_id": user_id}
    # 요청
    try:
        res = requests.post("http://127.0.0.1:3000/logout", json=data)
    except Exception as e:
        print("logout error : ", e)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(port=5000, debug=True)
# waitress-serve --port=5000 --channel-timeout=300 app:app

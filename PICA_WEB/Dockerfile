FROM python:3.10.11

WORKDIR /PICA_WEB
COPY . /PICA_WEB


RUN --mount=type=cache,target=/root/.cache/pip pip3 install -r requirements.txt



# 환경변수, 앱의 이름은 flask run 명령시 자동 인식이므로 생략
ENV FLASK_RUN_PORT 5000
ENV FLASK_RUN_HOST 0.0.0.0
# 기본이름이 아닌경우 엔트리 포인트를 직접 지정
ENV FLASK_APP app.py
# # 차후 프로덕션인 경우 수정
ENV FLASK_ENV development

# 포트 설정
EXPOSE 5000

# # 구동 명령
# ENTRYPOINT [ "flask" ]
# # 옵션
# CMD [ "run" ]

# uwsgi 실행
CMD ["uwsgi","uwsgi.ini"]
import pymysql

import modules.mariadb

# 비동기 처리
import asyncio
from functools import wraps


# db 연결
def connect_db():
    db = pymysql.connect(
        host="pica-database.coysatc2jipz.ap-northeast-2.rds.amazonaws.com",
        port=3306,
        user="root",
        password="12341234",
        charset="utf8",
    )
    sql = "use pica;"
    with db.cursor() as cursor:
        cursor.execute(sql)
    return db


# 스레드 처리 세팅
def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapped


# log 테이블 다 가져오기
def db_select_log():
    db = connect_db()

    sql = "select * from log;"
    results = None
    with db.cursor() as cursor:
        cursor.execute(sql)
        results = cursor.fetchall()

    db.close()
    return results


# user 테이블 다 가져오기
def db_select_user():
    db = connect_db()

    sql = "select * from user;"
    results = None
    with db.cursor() as cursor:
        cursor.execute(sql)
        results = cursor.fetchall()

    db.close()
    return results


#  db에서 url 조회시 사용
def db_select_url(id):
    """
    - descript = db에서 url 조회시 사용
    - arg
        - id : `int` = user테이블에서 고유 번호
    - return
        - result : `tuple` = (id, url_fun, url_sad, url_angry, user_id)
    """
    db = connect_db()

    sql = f"select * from url where user_id = {id};"
    result = None
    with db.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchone()

    db.close()
    return result


# db에서 url 조회시 사용
def db_select_mbti(id):
    """
    - descript = db에서 url 조회시 사용
    - arg
        - id : `int` = user테이블에서 고유 번호
    - return
        - result : `tuple` = (id, mbti, face, sex, nickname, user_id)
    """
    db = connect_db()

    sql = f"select mbti from vir_character where user_id = {id};"
    result = None
    with db.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchone()

    db.close()
    return result[0]


# user 테이블에서 user_name 조회시 사용
def db_select_user_name(id):
    """
    - descript = db에서 user_name 조회시 사용
    - arg
        - id : `int` = user테이블에서 고유 번호
    - return
        - result : `tuple` = (id, mbti, face, sex, nickname, user_id)
    """
    db = connect_db()

    sql = f"select user_name from user where id = {id};"
    result = None
    with db.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchone()

    db.close()
    return result[0]


# user 테이블에서 id 고유값 조회시 사용
def db_select_id(user_id):
    """
    - descript = user 테이블에서 id 고유값 조회시 사용
    - arg
        - name_value : `string` = user테이블 name 컬럼(아이디)
    - return
        - result[0] : `int` = id 고유값
    """
    db = connect_db()

    sql = f"select id from user where user_id = '{user_id}';"
    result = None
    with db.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchone()

    db.close()
    return result[0]


# db에서 원하는 테이블에 데이터 삽입
@async_action
async def db_insert(table_name, values):
    """
    - descript = db에서 원하는 테이블에 데이터 삽입
    - arg
        - table_name : `string` = user테이블 name 컬럼(아이디)
        - values : `int | string` = 데이터

        CREATE TABLE if not EXISTS vir_character (
        id INT(11) NOT NULL AUTO_INCREMENT,
        mbti VARCHAR(4) NOT NULL,
        face TINYINT(1) NOT NULL,
        sex TINYINT(1) NOT NULL,
        nickname VARCHAR(20) NOT NULL,
        user_id INT(11) NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES user(id)
        ON DELETE CASCADE
    );

    """
    db = connect_db()

    if table_name == "user":
        sql = f"insert into {table_name}(user_id, user_name) values({values});"
    elif table_name == "url":
        sql = f"insert into {table_name}(url_fun, url_sad, url_angry, user_id) values({values});"
    elif table_name == "log":
        sql = f"insert into {table_name}(question, answer, a_status, video_url, user_id, time) values({values});"
    elif table_name == "accum_emotion":
        sql = f"insert into {table_name}(user_id) values({values});"
    elif table_name == "vir_character":
        sql = f"insert into {table_name}(mbti, face, sex, nickname, user_id) values({values});"

    with db.cursor() as cursor:
        cursor.execute(sql)
    db.commit()
    db.close()


# user 테이블에서 데이터 삭제(casecade)
@async_action
async def db_delete(id_value):
    """
    - descript = user 테이블에서 데이터 삭제(casecade)
    - arg
        - id_value : `int` = user테이블의 고유값 삭제
    """
    db = connect_db()

    sql = f"delete from user where id = {id_value}"
    with db.cursor() as cursor:
        cursor.execute(sql)
    db.commit()
    db.close()


# log 테이블에서 해당 사용자의 대화기록 조회
def db_select_chatid(user_id):
    """
    - descript = log 테이블에서 해당 사용자의 대화기록 조회
    - arg
        - user_id :`int` = user테이블의 고유값 삭제
    """
    db = connect_db()

    sql = f"select id from log where user_id = '{user_id}';"
    result = None
    with db.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchall()

    db.close()
    # 마지막 대화 기록만 반환
    return result[-1][0]


# 대화로그 출력 함수
def db_select_chat_log(user_id):
    db = connect_db()

    result = None
    with db.cursor() as cursor:
        # 마지막 행의 accum_emotion 데이터 추출
        query = f"SELECT question, answer, DATE_FORMAT(time, '%Y-%m-%d %H:%i:%s') FROM log WHERE user_id = {user_id}"
        cursor.execute(query)
        result = cursor.fetchall()

    db.close()
    return result


# pieChart 데이터 함수
def pieChart_data(user_id):
    db = connect_db()

    result = None
    with db.cursor() as cursor:
        # 마지막 행의 accum_emotion 데이터 추출
        query = f"SELECT avg_happiness, avg_excited, avg_sadness, avg_bored, avg_disgust, avg_anger, avg_calm, avg_comfortable FROM accum_emotion WHERE user_id = {user_id}"
        cursor.execute(query)
        result = cursor.fetchone()

    # 백분율로 변환
    # 정수로 변환하여 백분율로 계산
    # print(result)
    if result is None:
        return []  # 빈 리스트 반환
    # 각 열의 값을 숫자로 변환
    values = [float(value) for value in result]
    total = sum(values)
    percentages = [value * 100 / total for value in values]
    # print(percentages)  # [0, 0, 0, 70, 0, 0, 5, 25]

    db.close()
    return percentages


# pieChart 데이터 함수
def total_chat_count_data(user_id):
    db = connect_db()

    result = None
    with db.cursor() as cursor:
        # 마지막 행의 accum_emotion 데이터 추출
        query = f"SELECT num_chat FROM accum_emotion WHERE user_id = {user_id}"
        cursor.execute(query)
        result = cursor.fetchone()

    db.close()
    return result


# lineChart 데이터 함수
def generate_chart_data(emotion, user_id):
    db = connect_db()

    emotion_list = {
        "행복": "happiness",
        "신남": "excited",
        "슬픔": "sadness",
        "지루": "bored",
        "혐오": "disgust",
        "분노": "anger",
        "고요": "calm",
        "편안": "comfortable",
    }
    emotion = emotion_list[emotion]
    result = None
    with db.cursor() as cursor:
        # 마지막 행의 accum_emotion 데이터 추출
        query = f"SELECT {emotion} FROM emotion WHERE user_id = {user_id}"
        cursor.execute(query)
        result = cursor.fetchall()

    if result is None:
        return []  # 빈 리스트 반환
    # 각 열의 값을 숫자로 변환
    # generate_chart_data-result [{'bored': Decimal('0.90')}, {'bored': Decimal('0.50')}, {'bored': Decimal('0.90')}]
    # generate_chart_data-values [0.9, 0.5, 0.9]
    values = [float(dic[0]) for dic in result]

    db.close()
    return values


if __name__ == "__main__":
    # db_insert("user", "name, password", "'test2', 456")
    # db_delete("user", 1)
    result = db_select_id("pica")
    # result = generate_chart_data("행복", 1)
    print(result)

import pymysql
from modules.mariadb import db

print("db 연결 ~ ", db)


# def db_select():
#     sql = "select * from user;"
#     results = None
#     with db.cursor() as cursor:
#         cursor.execute(sql)
#         results = cursor.fetchall()
#     return results


def db_select_url(id):
    """
    - descript = db에서 url 조회시 사용
    - arg
        - id : `int` = user테이블에서 고유 번호
    - return
        - result : `tuple` = (id, url_fun, url_sad, url_angry, user_id)
    """
    sql = f"select * from url where user_id = {id};"
    result = None
    with db.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchone()
    return result


def db_select_id(name_value):
    """
    - descript = user 테이블에서 id 고유값 조회시 사용
    - arg
        - name_value : `string` = user테이블 name 컬럼(아이디)
    - return
        - result[0] : `int` = id 고유값
    """
    sql = f"select id from user where name = '{name_value}';"
    result = None
    with db.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchone()
    return result[0]


def db_insert(table_name, values):
    """
    - descript = db에서 원하는 테이블에 데이터 삽입
    - arg
        - table_name : `string` = user테이블 name 컬럼(아이디)
        - values : `int | string` = 데이터
    """
    if table_name == "user":
        sql = f"insert into {table_name}(name) values('{values}');"
    elif table_name == "url":
        sql = f"insert into {table_name}(url_fun, url_sad, url_angry, user_id) values({values});"
    elif table_name == "log":
        sql = f"insert into {table_name}(question, answer, a_status, video_url, user_id) values({values});"
    elif table_name == "emotion":
        sql = f"insert into {table_name}(fun_c, sad_c, angry_c, user_id) values({values});"

    with db.cursor() as cursor:
        cursor.execute(sql)
    db.commit()


def db_delete(id_value):
    """
    - descript = db에서 user 테이블에서 데이터 삭제(casecade)
    - arg
        - id_value : `int` = user테이블의 고유값 삭제
    """
    sql = f"delete from user where id = {id_value}"
    with db.cursor() as cursor:
        cursor.execute(sql)
    db.commit()


if __name__ == "__main__":
    # db_insert("user", "name, password", "'test2', 456")
    # db_delete("user", 1)
    result = db_select_id("test2")
    print(result, type(result))

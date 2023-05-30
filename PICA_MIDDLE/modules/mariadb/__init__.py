import pymysql

# 데이터베이스 연결
db = pymysql.connect(host="pica-database.coysatc2jipz.ap-northeast-2.rds.amazonaws.com",port=3306, user="root", password="12341234", charset="utf8", connect_timeout=31536000)

# 커서 객체 생성
cursor = db.cursor()

# 데이터베이스 생성
sql = "CREATE DATABASE if not EXISTS pica;"
cursor.execute(sql)

# 데이터베이스 선택
sql = "USE pica;"
cursor.execute(sql)

# 테이블 생성
# password INT(11) NOT NULL,
sql = """
    CREATE TABLE if not EXISTS user (
        id INT(11) NOT NULL AUTO_INCREMENT,
        name VARCHAR(20) NOT NULL UNIQUE,
        PRIMARY KEY (id)
    );
"""
cursor.execute(sql)
sql = """
    CREATE TABLE if not EXISTS url (
        id INT(11) NOT NULL AUTO_INCREMENT,
        url_fun VARCHAR(100) NOT NULL,
        url_sad VARCHAR(100) NOT NULL,
        url_angry VARCHAR(100) NOT NULL,
        user_id INT(11) NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES user(id)
        ON DELETE CASCADE
    );
"""
cursor.execute(sql)
# log -> 영상 url 세팅
sql = """
    CREATE TABLE if not EXISTS log (
        id INT(11) NOT NULL AUTO_INCREMENT,
        question VARCHAR(300) NOT NULL,
        answer VARCHAR(300) NOT NULL,
        a_status INT(3) NOT NULL,
        q_status INT(3),
        video_url VARCHAR(500) NOT NULL,
        user_id INT(11) NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES user(id)
        ON DELETE CASCADE
    );
"""
cursor.execute(sql)
sql = """
    CREATE TABLE if not EXISTS emotion (
        id INT(11) NOT NULL AUTO_INCREMENT,
        fun_c INT(11) NOT NULL,
        sad_c INT(11) NOT NULL,
        angry_c INT(11) NOT NULL,
        user_id INT(11) NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES user(id)
        ON DELETE CASCADE
    );
"""
cursor.execute(sql)
cursor.close()
# 연결 종료

# db.close()

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

# user 테이블 생성
sql = """
    CREATE TABLE if not EXISTS user (
        id INT(11) NOT NULL AUTO_INCREMENT,
        name VARCHAR(20) NOT NULL UNIQUE,
        PRIMARY KEY (id)
    );
"""
cursor.execute(sql)

# url 테이블 생성
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

# log 테이블 생성
sql = """
    CREATE TABLE if not EXISTS log (
        id INT(11) NOT NULL AUTO_INCREMENT,
        question VARCHAR(300) NOT NULL,
        answer VARCHAR(300) NOT NULL,
        a_status INT(3) NOT NULL,
        video_url VARCHAR(500) NOT NULL,
        user_id INT(11) NOT NULL,
        time DATETIME NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES user(id)
        ON DELETE CASCADE
    );
"""
cursor.execute(sql)

# emotion 테이블 생성 (감정 분석 로그)
sql = """
    CREATE TABLE if not EXISTS emotion (
        id INT(11) NOT NULL AUTO_INCREMENT,
        happiness DECIMAL(5,2) NOT NULL,
        excited DECIMAL(5,2) NOT NULL,
        sadness DECIMAL(5,2) NOT NULL,
        bored DECIMAL(5,2) NOT NULL,
        disgust DECIMAL(5,2) NOT NULL,
        anger DECIMAL(5,2) NOT NULL,
        calm DECIMAL(5,2) NOT NULL,
        comfortable DECIMAL(5,2) NOT NULL,
        user_id INT(11) NOT NULL,
        log_id INT(11) NOT NULL,
        time DATETIME NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (log_id) REFERENCES log(id)
        ON DELETE CASCADE
    );
"""
cursor.execute(sql)

# vir_character 테이블 생성 (캐릭터 정보)
sql = """
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
cursor.execute(sql)

# accum_emotion 테이블 생성(감정분석 누적값)
sql = """
    CREATE TABLE if not EXISTS accum_emotion (
        id INT(11) NOT NULL AUTO_INCREMENT,
        sum_happiness DECIMAL(10,2) NOT NULL DEFAULT 0,
        sum_excited DECIMAL(10,2) NOT NULL DEFAULT 0,
        sum_sadness DECIMAL(10,2) NOT NULL DEFAULT 0,
        sum_bored DECIMAL(10,2) NOT NULL DEFAULT 0,
        sum_disgust DECIMAL(10,2) NOT NULL DEFAULT 0,
        sum_anger DECIMAL(10,2) NOT NULL DEFAULT 0,
        sum_calm DECIMAL(10,2) NOT NULL DEFAULT 0,
        sum_comfortable DECIMAL(10,2) NOT NULL DEFAULT 0,
        avg_happiness DECIMAL(5,3) NOT NULL DEFAULT 0,
        avg_excited DECIMAL(5,3) NOT NULL DEFAULT 0,
        avg_sadness DECIMAL(5,3) NOT NULL DEFAULT 0,
        avg_bored DECIMAL(5,3) NOT NULL DEFAULT 0,
        avg_disgust DECIMAL(5,3) NOT NULL DEFAULT 0,
        avg_anger DECIMAL(5,3) NOT NULL DEFAULT 0,
        avg_calm DECIMAL(5,3) NOT NULL DEFAULT 0,
        avg_comfortable DECIMAL(5,3) NOT NULL DEFAULT 0,
        num_chat SMALLINT NOT NULL DEFAULT 0,
        user_id INT(11) NOT NULL UNIQUE,
        PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES user(id)
        ON DELETE CASCADE
    );
"""
cursor.execute(sql)

# cursor 닫기
cursor.close()

# 연결 종료
# db.close()

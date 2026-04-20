# PostgreSQL 연결 정보와 세션 관리 함수
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://scott:tiger@172.16.8.101/scott_db"  # 본인 DB 정보로 수정
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 여기에 테이블 생성 코드 추가
CREATE_POST_TABLE = """
CREATE TABLE IF NOT EXISTS post (
    num SERIAL PRIMARY KEY,
    writer VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
)
"""

# DB 연결 시 테이블이 없으면 만듭니다.
with engine.connect() as connection:
    connection.execute(text(CREATE_POST_TABLE))
    connection.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. 추가함
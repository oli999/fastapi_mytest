from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db

app = FastAPI()

# 글 목록 조회
@app.get("/posts")
def list_posts(db: Session = Depends(get_db)):
    query = text("""
        SELECT num, writer, title, content, 
        TO_CHAR(created_at, 'YY.MM.DD DY AM HH:MI') as created_at
        FROM post ORDER BY num DESC
    """)
    result = db.execute(query)
    posts = [dict(row._mapping) for row in result.fetchall()]
    return posts

# 단일 글 조회
@app.get("/posts/{num}")
def get_post(num: int, db: Session = Depends(get_db)):
    query = text("SELECT num, writer, title, content, TO_CHAR(created_at, 'YY.MM.DD DY AM HH:MI') as created_at FROM post WHERE num=:num")
    row = db.execute(query, {"num": num}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return dict(row._mapping)

# 글 작성
@app.post("/posts")
def create_post(writer: str, title: str, content: str, db: Session = Depends(get_db)):
    query = text("INSERT INTO post (writer, title, content) VALUES (:writer, :title, :content) RETURNING num")
    result = db.execute(query, {"writer": writer, "title": title, "content": content})
    db.commit()
    new_num = result.fetchone()[0]
    return {"message": "Created", "num": new_num}

# 글 수정
@app.put("/posts/{num}")
def update_post(num: int, writer: str, title: str, content: str, db: Session = Depends(get_db)):
    # Check exists
    count_check = db.execute(text("SELECT COUNT(*) FROM post WHERE num=:num"), {"num": num}).scalar()
    if count_check == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    query = text("""
        UPDATE post
        SET writer=:writer, title=:title, content=:content
        WHERE num=:num
    """)
    db.execute(query, {"writer": writer, "title": title, "content": content, "num": num})
    db.commit()
    return {"message": "Updated"}

# 글 삭제
@app.delete("/posts/{num}")
def delete_post(num: int, db: Session = Depends(get_db)):
    count_check = db.execute(text("SELECT COUNT(*) FROM post WHERE num=:num"), {"num": num}).scalar()
    if count_check == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    db.execute(text("DELETE FROM post WHERE num=:num"), {"num": num})
    db.commit()
    return {"message": "Deleted"}
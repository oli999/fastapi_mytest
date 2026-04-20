

# pip install python-jose

import time
# Cookie 임포트 추가
from fastapi import FastAPI, Request, Depends, Form, Response, HTTPException, Cookie 
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session
# JWT 에러 처리 임포트 추가
from jose import jwt, JWTError, ExpiredSignatureError
from database import get_db

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# JWT 설정
SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

@app.post("/login")
def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),    # 실제로는 password 체크할 필요 없으나, 테스트용
):
    # 사용자 인증(테스트: 아이디만 체크)
    if username != "kimgura":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expire = int(time.time()) + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    payload = {
        "sub": username,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # 응답 쿠키로 access_token 전달
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    return {"access_token": token, "token_type": "bearer", "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60}

# 글 목록
@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    query = text("""
        SELECT num, writer, title, content, 
        TO_CHAR(created_at, 'YY.MM.DD DY AM HH:MI') as created_at
        FROM post ORDER BY num DESC
    """)
    result = db.execute(query)
    posts = result.fetchall()
    context = {
        "posts": posts
    }
    return templates.TemplateResponse(request=request, name="index.html", context=context)

# 글 작성 폼
@app.get("/create", response_class=HTMLResponse)
def create_form(request: Request):
    context = {}
    return templates.TemplateResponse(request=request, name="create.html", context=context)

# 글 작성 처리
@app.post("/create")
def create(writer: str = Form(...), title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    query = text("INSERT INTO post (writer, title, content) VALUES (:writer, :title, :content)")
    db.execute(query, {"writer": writer, "title": title, "content": content})
    db.commit()
    return RedirectResponse("/", status_code=302)

# 글 수정 폼
@app.get("/edit/{num}", response_class=HTMLResponse)
def edit_form(num: int, request: Request, db: Session = Depends(get_db)):
    query = text("SELECT * FROM post WHERE num=:num")
    row = db.execute(query, {"num": num}).fetchone()
    if not row:
        return HTMLResponse("글을 찾을 수 없습니다.", status_code=404)
    post = dict(row._mapping)
    context = {"post": post}
    return templates.TemplateResponse(request=request, name="edit.html", context=context)

# 글 수정 처리
@app.post("/edit/{num}")
def edit(num: int, writer: str = Form(...), title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    query = text("""
        UPDATE post SET writer=:writer, title=:title, content=:content
        WHERE num=:num
    """)
    db.execute(query, {"writer": writer, "title": title, "content": content, "num": num})
    db.commit()
    return RedirectResponse("/", status_code=302)

# 글 삭제
@app.get("/delete/{num}")
def delete(num: int, db: Session = Depends(get_db)):
    query = text("DELETE FROM post WHERE num=:num")
    db.execute(query, {"num": num})
    db.commit()
    return RedirectResponse("/", status_code=302)

# 토큰 검증 테스트용 API
@app.get("/ping")
def ping(access_token: str | None = Cookie(default=None)):
    # 1. 쿠키에 토큰이 아예 없는 경우 (비로그인)
    if not access_token:
        raise HTTPException(status_code=401, detail="토큰이 없습니다. 먼저 로그인 해주세요.")
    
    try:
        # 2. 토큰 디코딩 및 검증 (서명 확인, 만료일자 자동 체크)
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(status_code=401, detail="토큰에 사용자 정보가 없습니다.")
            
        # 3. 검증 성공 시 환영 메시지 반환
        return {
            "message": "pong", 
            "user": username, 
            "status": "토큰 검증 완벽 성공! 32GB 서버가 당신을 환영합니다."
        }
        
    except ExpiredSignatureError:
        # 시간이 지나서 토큰이 만료된 경우
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다. 다시 로그인 해주세요.")
        
    except JWTError:
        # 서명이 조작되었거나 형식이 잘못된 경우
        raise HTTPException(status_code=401, detail="유효하지 않거나 조작된 토큰입니다.")
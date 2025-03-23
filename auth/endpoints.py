import os
import bcrypt
import jwt
import datetime

import psycopg
from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from dotenv import load_dotenv
from uuid import uuid4
from database.database import connect_to_db, get_user_by_id

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router = APIRouter()

class UserSignup(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

def create_access_token(user_id: str):
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str):
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token")

def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


def get_current_user(token: str = Security(oauth2_scheme)):
    print(f"Received token: {token}")

    try:
        user_id = decode_access_token(token)
        print(f"Decoded user ID: {user_id}")
    except Exception as e:
        print(f"Token decoding failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_id(user_id)

    if user is None:
        print(f"User not found in database for ID: {user_id}")
        raise HTTPException(status_code=401, detail="User not found")

    print(f"User found: {user}")

    return {"id": str(user["id"]), "username": user["username"], "email": user["email"]}


@router.post("/signup", response_model=TokenResponse)
def signup(user: UserSignup):
    conn = connect_to_db()
    if conn:
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    raise HTTPException(status_code=400, detail="Email is already in use")

            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
                existing_username = cursor.fetchone()
                if existing_username:
                    raise HTTPException(status_code=400, detail="Username is already taken")

            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (id, username, email, password_hash) VALUES (%s, %s, %s, %s) RETURNING id",
                    (str(uuid4()), user.username, user.email, hashed_password))
                user_id = cursor.fetchone()[0]
                conn.commit()
        except psycopg.errors.UniqueViolation:
            raise HTTPException(status_code=400, detail="Username or email already taken")
        finally:
            conn.close()

        access_token = create_access_token(str(user_id))
        refresh_token = create_refresh_token(str(user_id))
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    raise HTTPException(status_code=500, detail="Database connection error")

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, password_hash FROM users WHERE email = %s", (user.email,))
            db_user = cursor.fetchone()
        conn.close()

        if db_user and bcrypt.checkpw(user.password.encode('utf-8'), db_user[1].encode('utf-8')):
            access_token = create_access_token(str(db_user[0]))
            refresh_token = create_refresh_token(str(db_user[0]))
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }

    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(request: RefreshTokenRequest):
    user_id = decode_refresh_token(request.refresh_token)
    new_access_token = create_access_token(user_id)
    return {
        "access_token": new_access_token,
        "refresh_token": request.refresh_token,
        "token_type": "bearer"
    }

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
import os
import psycopg
import bcrypt
import jwt
import datetime
from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def connect_to_db():
    DATABASE_URL = os.getenv("DATABASE_URL")
    try:
        conn = psycopg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

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
    token_type: str

def create_access_token(user_id: str):
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token: str = Security(oauth2_scheme)):
    user_id = decode_access_token(token)
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
        conn.close()
        if user:
            return {"id": str(user[0]), "username": user[1], "email": user[2]}
    raise HTTPException(status_code=401, detail="User not found")

# Signup Route
@router.post("/signup", response_model=TokenResponse)
def signup(user: UserSignup):
    conn = connect_to_db()
    if conn:
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO users (id, username, email, password_hash) VALUES (%s, %s, %s, %s) RETURNING id",
                               (str(uuid4()), user.username, user.email, hashed_password))
                user_id = cursor.fetchone()[0]
                conn.commit()
        except psycopg.errors.UniqueViolation:
            raise HTTPException(status_code=400, detail="Username or email already taken")
        finally:
            conn.close()

        token = create_access_token(str(user_id))
        return {"access_token": token, "token_type": "bearer"}

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
            token = create_access_token(str(db_user[0]))
            return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=401, detail="Invalid credentials")

# Get current user (Protected route)
@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

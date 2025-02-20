from fastapi import APIRouter, HTTPException
import psycopg
from pydantic import BaseModel
from uuid import uuid4

class User(BaseModel):
    username: str
    email: str
    password_hash: str

def connect_to_db():
    from dotenv import load_dotenv
    import os
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

    try:
        conn = psycopg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# Helper function to fetch user by ID
def get_user_by_id(user_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
        conn.close()
        return user
    return None

router = APIRouter()

@router.post("/")
def create_user(user: User):
    conn = connect_to_db()
    if conn:
        user_id = str(uuid4())  # generate a unique ID for the user
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id;
            """, (user_id, user.username, user.email, user.password_hash))
            conn.commit()
        conn.close()
        return {"id": user_id, "username": user.username, "email": user.email}
    raise HTTPException(status_code=500, detail="Error creating user.")

@router.get("/{user_id}")
def read_user(user_id: str):
    user = get_user_by_id(user_id)
    if user:
        return {"id": user[0], "username": user[1], "email": user[2], "created_at": user[4]}
    raise HTTPException(status_code=404, detail="User not found")

@router.get("/")
def read_all_users():
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
        conn.close()
        return [{"id": user[0], "username": user[1], "email": user[2], "created_at": user[4]} for user in users]
    raise HTTPException(status_code=500, detail="Error fetching users.")

@router.put("/{user_id}")
def update_user(user_id: str, user: User):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET username = %s, email = %s, password_hash = %s 
                WHERE id = %s
            """, (user.username, user.email, user.password_hash, user_id))
            conn.commit()
        conn.close()
        return {"message": "User updated successfully"}
    raise HTTPException(status_code=500, detail="Error updating user.")

@router.delete("/{user_id}")
def delete_user(user_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
        conn.close()
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=500, detail="Error deleting user.")

import os
import psycopg
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()


def connect_to_db():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="Database URL is not set in environment variables")

    try:
        return psycopg.connect(DATABASE_URL)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")


def get_user_by_id(user_id: str):
    try:
        with connect_to_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, password_hash FROM users WHERE id = %s", (user_id,)
                )
                user = cursor.fetchone()

        if user:
            return {
                "id": str(user[0]),
                "username": user[1],
                "email": user[2],
                "password_hash": user[3],
            }
        else:
            raise HTTPException(status_code=404, detail="User not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

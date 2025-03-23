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
    conn = connect_to_db()
    if conn:
        conn.row_factory = psycopg.rows.dict_row

        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

        conn.close()
        return user
    return None

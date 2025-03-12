from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth.endpoints import get_current_user
from database.database import connect_to_db, get_user_by_id

router = APIRouter()

class UserUpdate(BaseModel):
    username: str
    email: str

@router.get("/")
def read_all_users(current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    with conn.cursor() as cursor:
        cursor.execute("SELECT id, username, email, created_at FROM users")
        users = cursor.fetchall()
    conn.close()

    return [{"id": str(user[0]), "username": user[1], "email": user[2], "created_at": user[3]} for user in users]

@router.get("/{user_id}")
def read_user(user_id: str, current_user: dict = Depends(get_current_user)):
    user = get_user_by_id(user_id)
    if user:
        return {"id": str(user[0]), "username": user[1], "email": user[2], "created_at": user[3]}
    raise HTTPException(status_code=404, detail="User not found")

@router.put("/{user_id}")
def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to update this user")

    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE users 
            SET username = %s, email = %s 
            WHERE id = %s
        """, (user_data.username, user_data.email, user_id))
        conn.commit()
    conn.close()

    return {"message": "User updated successfully"}

@router.delete("/{user_id}")
def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to delete this user")

    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    conn.close()

    return {"message": "User deleted successfully"}
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from auth.endpoints import get_current_user
from database.database import connect_to_db, get_user_by_id

router = APIRouter()


class UserUpdate(BaseModel):
    username: str
    email: EmailStr


@router.get("/")
def read_all_users(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Unauthorized to fetch all users")

    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, email, created_at FROM users")
            users = cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")
    finally:
        conn.close()

    return [
        {"id": str(user[0]), "username": user[1], "email": user[2], "created_at": user[3]}
        for user in users
    ]


@router.get("/{user_id}")
def read_user(user_id: str, current_user: dict = Depends(get_current_user)):
    user = get_user_by_id(user_id)
    if user:
        return {"id": str(user[0]), "username": user[1], "email": user[2]}
    raise HTTPException(status_code=404, detail="User not found")


@router.put("/{user_id}")
def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to update this user")

    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")

            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (user_data.email, user_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email is already in use")

            cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (user_data.username, user_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Username is already taken")

            cursor.execute("""
                UPDATE users 
                SET username = %s, email = %s 
                WHERE id = %s
            """, (user_data.username, user_data.email, user_id))
            conn.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")
    finally:
        conn.close()

    return {"message": "User updated successfully"}


@router.delete("/{user_id}")
def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to delete this user")

    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")

            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")
    finally:
        conn.close()

    return {"message": "User deleted successfully"}

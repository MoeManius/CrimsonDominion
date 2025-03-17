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
    try:
        with connect_to_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, username, email, created_at FROM users")
                users = cursor.fetchall()

        return [
            {"id": str(user[0]), "username": user[1], "email": user[2], "created_at": user[3]}
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@router.get("/{user_id}")
def read_user(user_id: str, current_user: dict = Depends(get_current_user)):
    user = get_user_by_id(user_id)
    if user:
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    raise HTTPException(status_code=404, detail="User not found")

@router.put("/{user_id}")
def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to update this user")

    try:
        with connect_to_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (user_data.email, user_id))
                existing_email = cursor.fetchone()
                if existing_email:
                    raise HTTPException(status_code=400, detail="Email is already in use")

                cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (user_data.username, user_id))
                existing_username = cursor.fetchone()
                if existing_username:
                    raise HTTPException(status_code=400, detail="Username is already taken")

                cursor.execute("""
                    UPDATE users 
                    SET username = %s, email = %s 
                    WHERE id = %s
                """, (user_data.username, user_data.email, user_id))
                conn.commit()

        return {"message": "User updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@router.delete("/{user_id}")
def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a user."""
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to delete this user")

    try:
        with connect_to_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                conn.commit()

        return {"message": "User deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

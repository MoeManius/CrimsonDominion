from fastapi import APIRouter, HTTPException
import psycopg
from pydantic import BaseModel
from uuid import uuid4

class UserBuilding(BaseModel):
    user_id: str
    building_id: str
    planet_id: str
    level: int

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

# Helper function to fetch user building by ID
def get_user_building_by_id(user_building_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_buildings WHERE id = %s", (user_building_id,))
            user_building = cursor.fetchone()
        conn.close()
        return user_building
    return None

router = APIRouter()

@router.post("/")
def create_user_building(user_building: UserBuilding):
    conn = connect_to_db()
    if conn:
        user_building_id = str(uuid4())  # Generate unique ID
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_buildings (id, user_id, building_id, planet_id, level) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id;
            """, (user_building_id, user_building.user_id, user_building.building_id, user_building.planet_id, user_building.level))
            conn.commit()
        conn.close()
        return {"id": user_building_id, "user_id": user_building.user_id, "building_id": user_building.building_id, "planet_id": user_building.planet_id, "level": user_building.level}
    raise HTTPException(status_code=500, detail="Error creating user building.")

@router.get("/{user_building_id}")
def read_user_building(user_building_id: str):
    user_building = get_user_building_by_id(user_building_id)
    if user_building:
        return {"id": user_building[0], "user_id": user_building[1], "building_id": user_building[2], "planet_id": user_building[3], "level": user_building[4]}
    raise HTTPException(status_code=404, detail="User building not found")

@router.get("/")
def read_all_user_buildings():
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_buildings")
            user_buildings = cursor.fetchall()
        conn.close()
        return [{"id": ub[0], "user_id": ub[1], "building_id": ub[2], "planet_id": ub[3], "level": ub[4]} for ub in user_buildings]
    raise HTTPException(status_code=500, detail="Error fetching user buildings.")

@router.put("/{user_building_id}")
def update_user_building(user_building_id: str, user_building: UserBuilding):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE user_buildings 
                SET user_id = %s, building_id = %s, planet_id = %s, level = %s 
                WHERE id = %s
            """, (user_building.user_id, user_building.building_id, user_building.planet_id, user_building.level, user_building_id))
            conn.commit()
        conn.close()
        return {"message": "User building updated successfully"}
    raise HTTPException(status_code=500, detail="Error updating user building.")

@router.delete("/{user_building_id}")
def delete_user_building(user_building_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM user_buildings WHERE id = %s", (user_building_id,))
            conn.commit()
        conn.close()
        return {"message": "User building deleted successfully"}
    raise HTTPException(status_code=500, detail="Error deleting user building.")

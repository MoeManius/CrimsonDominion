from fastapi import APIRouter, HTTPException, Depends
import psycopg
from pydantic import BaseModel
from uuid import uuid4
from auth.endpoints import get_current_user
from database.database import connect_to_db

class UserBuilding(BaseModel):
    building_id: str
    planet_id: str
    level: int

router = APIRouter()

@router.post("/")
def create_user_building(user_building: UserBuilding, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    user_building_id = str(uuid4())
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_buildings (id, user_id, building_id, planet_id, level) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id;
            """, (user_building_id, current_user["id"], user_building.building_id, user_building.planet_id, user_building.level))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user building: {str(e)}")
    finally:
        conn.close()

    return {
        "id": user_building_id,
        "user_id": current_user["id"],
        "building_id": user_building.building_id,
        "planet_id": user_building.planet_id,
        "level": user_building.level
    }

@router.get("/{user_building_id}")
def read_user_building(user_building_id: str, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, building_id, planet_id, level 
                FROM user_buildings WHERE id = %s
            """, (user_building_id,))
            user_building = cursor.fetchone()
    finally:
        conn.close()

    if user_building:
        building_data = {
            "id": user_building[0],
            "user_id": user_building[1],
            "building_id": user_building[2],
            "planet_id": user_building[3],
            "level": user_building[4]
        }
        if current_user["id"] == building_data["user_id"]:
            return building_data
        raise HTTPException(status_code=403, detail="Unauthorized to view this user building")

    raise HTTPException(status_code=404, detail="User building not found")

@router.get("/")
def read_all_user_buildings(current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, building_id, planet_id, level 
                FROM user_buildings WHERE user_id = %s
            """, (current_user["id"],))
            user_buildings = cursor.fetchall()
    finally:
        conn.close()

    return [
        {
            "id": ub[0],
            "building_id": ub[1],
            "planet_id": ub[2],
            "level": ub[3]
        } for ub in user_buildings
    ]

@router.put("/{user_building_id}")
def update_user_building(user_building_id: str, user_building: UserBuilding, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM user_buildings WHERE id = %s", (user_building_id,))
            existing_user_building = cursor.fetchone()
            if not existing_user_building:
                raise HTTPException(status_code=404, detail="User building not found")
            if existing_user_building[0] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Unauthorized to update this user building")

            cursor.execute("""
                UPDATE user_buildings 
                SET building_id = %s, planet_id = %s, level = %s 
                WHERE id = %s
            """, (user_building.building_id, user_building.planet_id, user_building.level, user_building_id))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user building: {str(e)}")
    finally:
        conn.close()

    return {"message": "User building updated successfully"}

@router.delete("/{user_building_id}")
def delete_user_building(user_building_id: str, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM user_buildings WHERE id = %s", (user_building_id,))
            existing_user_building = cursor.fetchone()
            if not existing_user_building:
                raise HTTPException(status_code=404, detail="User building not found")
            if existing_user_building[0] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Unauthorized to delete this user building")

            cursor.execute("DELETE FROM user_buildings WHERE id = %s", (user_building_id,))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user building: {str(e)}")
    finally:
        conn.close()

    return {"message": "User building deleted successfully"}

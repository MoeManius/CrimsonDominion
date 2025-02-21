from fastapi import APIRouter, HTTPException
import psycopg
from pydantic import BaseModel
from uuid import uuid4
from psycopg.types.json import Json

class UserFleet(BaseModel):
    user_id: str
    planet_id: str
    ships: dict  # {"fighter": 10, "bomber": 5, "cruiser": 2}

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

def get_user_fleet_by_id(user_fleet_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_fleets WHERE id = %s", (user_fleet_id,))
            user_fleet = cursor.fetchone()
        conn.close()
        return user_fleet
    return None

router = APIRouter()

@router.post("/")
def create_user_fleet(user_fleet: UserFleet):
    conn = connect_to_db()
    if conn:
        user_fleet_id = str(uuid4())  # Generate unique ID
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_fleets (id, user_id, planet_id, ships) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id;
            """, (user_fleet_id, user_fleet.user_id, user_fleet.planet_id, psycopg.types.json.Json(user_fleet.ships)))
            conn.commit()
        conn.close()
        return {"id": user_fleet_id, "user_id": user_fleet.user_id, "planet_id": user_fleet.planet_id, "ships": user_fleet.ships}
    raise HTTPException(status_code=500, detail="Error creating user fleet.")

@router.get("/{user_fleet_id}")
def read_user_fleet(user_fleet_id: str):
    user_fleet = get_user_fleet_by_id(user_fleet_id)
    if user_fleet:
        return {"id": user_fleet[0], "user_id": user_fleet[1], "planet_id": user_fleet[2], "ships": user_fleet[3]}
    raise HTTPException(status_code=404, detail="User fleet not found")

@router.get("/")
def read_all_user_fleets():
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_fleets")
            user_fleets = cursor.fetchall()
        conn.close()
        return [{"id": uf[0], "user_id": uf[1], "planet_id": uf[2], "ships": uf[3]} for uf in user_fleets]
    raise HTTPException(status_code=500, detail="Error fetching user fleets.")

@router.put("/{user_fleet_id}")
def update_user_fleet(user_fleet_id: str, user_fleet: UserFleet):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE user_fleets 
                SET user_id = %s, planet_id = %s, ships = %s 
                WHERE id = %s
            """, (user_fleet.user_id, user_fleet.planet_id, psycopg.types.json.Json(user_fleet.ships), user_fleet_id))
            conn.commit()
        conn.close()
        return {"message": "User fleet updated successfully"}
    raise HTTPException(status_code=500, detail="Error updating user fleet.")

@router.delete("/{user_fleet_id}")
def delete_user_fleet(user_fleet_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM user_fleets WHERE id = %s", (user_fleet_id,))
            conn.commit()
        conn.close()
        return {"message": "User fleet deleted successfully"}
    raise HTTPException(status_code=500, detail="Error deleting user fleet.")

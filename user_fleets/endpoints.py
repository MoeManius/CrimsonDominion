from fastapi import APIRouter, HTTPException, Depends
import psycopg
from pydantic import BaseModel
from uuid import uuid4
import json
from auth.endpoints import get_current_user
from database.database import connect_to_db

class UserFleet(BaseModel):
    planet_id: str
    ships: dict

router = APIRouter()

@router.post("/")
def create_user_fleet(user_fleet: UserFleet, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    fleet_id = str(uuid4())
    ships_json = json.dumps(user_fleet.ships)

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_fleets (id, user_id, planet_id, ships) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id;
            """, (fleet_id, current_user["id"], user_fleet.planet_id, ships_json))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user fleet: {str(e)}")
    finally:
        conn.close()

    return {"id": fleet_id, "user_id": current_user["id"], "planet_id": user_fleet.planet_id, "ships": user_fleet.ships}

@router.get("/{fleet_id}")
def read_user_fleet(fleet_id: str, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, planet_id, ships 
                FROM user_fleets WHERE id = %s
            """, (fleet_id,))
            fleet = cursor.fetchone()
    finally:
        conn.close()

    if fleet:
        fleet_data = {
            "id": fleet[0],
            "user_id": fleet[1],
            "planet_id": fleet[2],
            "ships": json.loads(fleet[3])
        }
        if current_user["id"] == fleet_data["user_id"]:
            return fleet_data
        raise HTTPException(status_code=403, detail="Unauthorized to view this fleet")

    raise HTTPException(status_code=404, detail="Fleet not found")

@router.get("/")
def read_all_user_fleets(current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, planet_id, ships 
                FROM user_fleets WHERE user_id = %s
            """, (current_user["id"],))
            fleets = cursor.fetchall()
    finally:
        conn.close()

    return [
        {
            "id": f[0],
            "planet_id": f[1],
            "ships": json.loads(f[2])
        } for f in fleets
    ]

@router.put("/{fleet_id}")
def update_user_fleet(fleet_id: str, user_fleet: UserFleet, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    ships_json = json.dumps(user_fleet.ships)

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM user_fleets WHERE id = %s", (fleet_id,))
            existing_fleet = cursor.fetchone()
            if not existing_fleet:
                raise HTTPException(status_code=404, detail="Fleet not found")
            if existing_fleet[0] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Unauthorized to update this fleet")

            cursor.execute("""
                UPDATE user_fleets 
                SET planet_id = %s, ships = %s 
                WHERE id = %s
            """, (user_fleet.planet_id, ships_json, fleet_id))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating fleet: {str(e)}")
    finally:
        conn.close()

    return {"message": "Fleet updated successfully"}

@router.delete("/{fleet_id}")
def delete_user_fleet(fleet_id: str, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM user_fleets WHERE id = %s", (fleet_id,))
            existing_fleet = cursor.fetchone()
            if not existing_fleet:
                raise HTTPException(status_code=404, detail="Fleet not found")
            if existing_fleet[0] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Unauthorized to delete this fleet")

            cursor.execute("DELETE FROM user_fleets WHERE id = %s", (fleet_id,))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting fleet: {str(e)}")
    finally:
        conn.close()

    return {"message": "Fleet deleted successfully"}

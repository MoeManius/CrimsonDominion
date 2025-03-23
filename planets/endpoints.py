from fastapi import APIRouter, HTTPException, Depends
import psycopg
from pydantic import BaseModel
from uuid import uuid4
import json
from auth.endpoints import get_current_user
from database.database import connect_to_db

class Planet(BaseModel):
    name: str
    resources: dict
    discovered_at: str
    claimed_at: str

router = APIRouter()

@router.post("/")
def create_planet(planet: Planet, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    planet_id = str(uuid4())
    resources_json = json.dumps(planet.resources)

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO planets (id, name, owner_id, resources, discovered_at, claimed_at) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                RETURNING id;
            """, (planet_id, planet.name, current_user["id"], resources_json, planet.discovered_at, planet.claimed_at))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating planet: {str(e)}")
    finally:
        conn.close()

    return {"id": planet_id, "name": planet.name, "owner_id": current_user["id"]}

@router.get("/{planet_id}")
def read_planet(planet_id: str, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, owner_id, resources, discovered_at, claimed_at FROM planets WHERE id = %s", (planet_id,))
            planet = cursor.fetchone()
    finally:
        conn.close()

    if planet:
        planet_data = {
            "id": planet[0],
            "name": planet[1],
            "owner_id": planet[2],
            "resources": json.loads(planet[3]),
            "discovered_at": planet[4],
            "claimed_at": planet[5]
        }
        if current_user["id"] == planet_data["owner_id"]:
            return planet_data
        raise HTTPException(status_code=403, detail="Unauthorized to view this planet")

    raise HTTPException(status_code=404, detail="Planet not found")

@router.get("/")
def read_all_planets(current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, resources, discovered_at, claimed_at 
                FROM planets WHERE owner_id = %s
            """, (current_user["id"],))
            planets = cursor.fetchall()
    finally:
        conn.close()

    return [
        {
            "id": p[0],
            "name": p[1],
            "resources": json.loads(p[2]),
            "discovered_at": p[3],
            "claimed_at": p[4]
        } for p in planets
    ]

@router.put("/{planet_id}")
def update_planet(planet_id: str, planet: Planet, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    resources_json = json.dumps(planet.resources)

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT owner_id FROM planets WHERE id = %s", (planet_id,))
            existing_planet = cursor.fetchone()
            if not existing_planet:
                raise HTTPException(status_code=404, detail="Planet not found")
            if existing_planet[0] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Unauthorized to update this planet")

            cursor.execute("""
                UPDATE planets 
                SET name = %s, resources = %s, discovered_at = %s, claimed_at = %s 
                WHERE id = %s
            """, (planet.name, resources_json, planet.discovered_at, planet.claimed_at, planet_id))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating planet: {str(e)}")
    finally:
        conn.close()

    return {"message": "Planet updated successfully"}

@router.delete("/{planet_id}")
def delete_planet(planet_id: str, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT owner_id FROM planets WHERE id = %s", (planet_id,))
            existing_planet = cursor.fetchone()
            if not existing_planet:
                raise HTTPException(status_code=404, detail="Planet not found")
            if existing_planet[0] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Unauthorized to delete this planet")

            cursor.execute("DELETE FROM planets WHERE id = %s", (planet_id,))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting planet: {str(e)}")
    finally:
        conn.close()

    return {"message": "Planet deleted successfully"}

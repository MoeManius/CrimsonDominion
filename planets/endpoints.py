from fastapi import APIRouter, HTTPException
import psycopg
from pydantic import BaseModel
from uuid import uuid4
import json

class Planet(BaseModel):
    name: str
    owner_id: str
    resources: dict
    discovered_at: str
    claimed_at: str

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

def get_planet_by_id(planet_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM planets WHERE id = %s", (planet_id,))
            planet = cursor.fetchone()
        conn.close()
        return planet
    return None

router = APIRouter()

@router.post("/")
def create_planet(planet: Planet):
    conn = connect_to_db()
    if conn:
        planet_id = str(uuid4())
        resources_json = json.dumps(planet.resources)

        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO planets (id, name, owner_id, resources, discovered_at, claimed_at) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                RETURNING id;
            """, (planet_id, planet.name, planet.owner_id, resources_json, planet.discovered_at, planet.claimed_at))
            conn.commit()
        conn.close()
        return {"id": planet_id, "name": planet.name, "owner_id": planet.owner_id}
    raise HTTPException(status_code=500, detail="Error creating planet.")

@router.get("/{planet_id}")
def read_planet(planet_id: str):
    planet = get_planet_by_id(planet_id)
    if planet:
        return {
            "id": planet[0],
            "name": planet[1],
            "owner_id": planet[2],
            "resources": json.loads(planet[3]),
            "discovered_at": planet[4],
            "claimed_at": planet[5]
        }
    raise HTTPException(status_code=404, detail="Planet not found")

@router.get("/")
def read_all_planets():
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM planets")
            planets = cursor.fetchall()
        conn.close()
        return [{
            "id": planet[0],
            "name": planet[1],
            "owner_id": planet[2],
            "resources": json.loads(planet[3]),
            "discovered_at": planet[4],
            "claimed_at": planet[5]
        } for planet in planets]
    raise HTTPException(status_code=500, detail="Error fetching planets.")

@router.put("/{planet_id}")
def update_planet(planet_id: str, planet: Planet):
    conn = connect_to_db()
    if conn:
        resources_json = json.dumps(planet.resources)

        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE planets 
                SET name = %s, owner_id = %s, resources = %s, discovered_at = %s, claimed_at = %s 
                WHERE id = %s
            """, (planet.name, planet.owner_id, resources_json, planet.discovered_at, planet.claimed_at, planet_id))
            conn.commit()
        conn.close()
        return {"message": "Planet updated successfully"}
    raise HTTPException(status_code=500, detail="Error updating planet.")

@router.delete("/{planet_id}")
def delete_planet(planet_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM planets WHERE id = %s", (planet_id,))
            conn.commit()
        conn.close()
        return {"message": "Planet deleted successfully"}
    raise HTTPException(status_code=500, detail="Error deleting planet.")

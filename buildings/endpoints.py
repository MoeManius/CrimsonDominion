from fastapi import APIRouter, HTTPException
import psycopg
from pydantic import BaseModel
from uuid import uuid4

class Building(BaseModel):
    name: str
    type: str
    resource_cost: dict  # JSON format for resource cost

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

# Helper function to fetch building by ID
def get_building_by_id(building_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM buildings WHERE id = %s", (building_id,))
            building = cursor.fetchone()
        conn.close()
        return building
    return None

router = APIRouter()

@router.post("/")
def create_building(building: Building):
    conn = connect_to_db()
    if conn:
        building_id = str(uuid4())  # Generate unique ID
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO buildings (id, name, type, resource_cost) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id;
            """, (building_id, building.name, building.type, str(building.resource_cost)))
            conn.commit()
        conn.close()
        return {"id": building_id, "name": building.name, "type": building.type, "resource_cost": building.resource_cost}
    raise HTTPException(status_code=500, detail="Error creating building.")

@router.get("/{building_id}")
def read_building(building_id: str):
    building = get_building_by_id(building_id)
    if building:
        return {"id": building[0], "name": building[1], "type": building[2], "resource_cost": building[3]}
    raise HTTPException(status_code=404, detail="Building not found")

@router.get("/")
def read_all_buildings():
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM buildings")
            buildings = cursor.fetchall()
        conn.close()
        return [{"id": b[0], "name": b[1], "type": b[2], "resource_cost": b[3]} for b in buildings]
    raise HTTPException(status_code=500, detail="Error fetching buildings.")

@router.put("/{building_id}")
def update_building(building_id: str, building: Building):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE buildings 
                SET name = %s, type = %s, resource_cost = %s 
                WHERE id = %s
            """, (building.name, building.type, str(building.resource_cost), building_id))
            conn.commit()
        conn.close()
        return {"message": "Building updated successfully"}
    raise HTTPException(status_code=500, detail="Error updating building.")

@router.delete("/{building_id}")
def delete_building(building_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM buildings WHERE id = %s", (building_id,))
            conn.commit()
        conn.close()
        return {"message": "Building deleted successfully"}
    raise HTTPException(status_code=500, detail="Error deleting building.")

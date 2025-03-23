from fastapi import APIRouter, HTTPException, Depends
import psycopg
from pydantic import BaseModel
from uuid import uuid4
import json
from auth.endpoints import get_current_user
from database.database import connect_to_db

class Building(BaseModel):
    name: str
    type: str
    resource_cost: dict

router = APIRouter()

@router.post("/")
def create_building(building: Building, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    building_id = str(uuid4())
    resource_cost_json = json.dumps(building.resource_cost)

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO buildings (id, owner_id, name, type, resource_cost) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id;
            """, (building_id, current_user["id"], building.name, building.type, resource_cost_json))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating building: {str(e)}")
    finally:
        conn.close()

    return {
        "id": building_id,
        "owner_id": current_user["id"],
        "name": building.name,
        "type": building.type,
        "resource_cost": building.resource_cost
    }

@router.get("/{building_id}")
def read_building(building_id: str, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, owner_id, name, type, resource_cost 
                FROM buildings WHERE id = %s
            """, (building_id,))
            building = cursor.fetchone()
    finally:
        conn.close()

    if building:
        building_data = {
            "id": building[0],
            "owner_id": building[1],
            "name": building[2],
            "type": building[3],
            "resource_cost": json.loads(building[4])
        }
        if current_user["id"] == building_data["owner_id"]:
            return building_data
        raise HTTPException(status_code=403, detail="Unauthorized to view this building")

    raise HTTPException(status_code=404, detail="Building not found")

@router.get("/")
def read_all_buildings(current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, type, resource_cost 
                FROM buildings WHERE owner_id = %s
            """, (current_user["id"],))
            buildings = cursor.fetchall()
    finally:
        conn.close()

    return [
        {
            "id": b[0],
            "name": b[1],
            "type": b[2],
            "resource_cost": json.loads(b[3])
        } for b in buildings
    ]

@router.put("/{building_id}")
def update_building(building_id: str, building: Building, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    resource_cost_json = json.dumps(building.resource_cost)

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT owner_id FROM buildings WHERE id = %s", (building_id,))
            existing_building = cursor.fetchone()
            if not existing_building:
                raise HTTPException(status_code=404, detail="Building not found")
            if existing_building[0] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Unauthorized to update this building")

            cursor.execute("""
                UPDATE buildings 
                SET name = %s, type = %s, resource_cost = %s 
                WHERE id = %s
            """, (building.name, building.type, resource_cost_json, building_id))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating building: {str(e)}")
    finally:
        conn.close()

    return {"message": "Building updated successfully"}

@router.delete("/{building_id}")
def delete_building(building_id: str, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT owner_id FROM buildings WHERE id = %s", (building_id,))
            existing_building = cursor.fetchone()
            if not existing_building:
                raise HTTPException(status_code=404, detail="Building not found")
            if existing_building[0] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Unauthorized to delete this building")

            cursor.execute("DELETE FROM buildings WHERE id = %s", (building_id,))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting building: {str(e)}")
    finally:
        conn.close()

    return {"message": "Building deleted successfully"}

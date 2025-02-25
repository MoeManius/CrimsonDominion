from fastapi import APIRouter, HTTPException
import psycopg
from pydantic import BaseModel
from uuid import uuid4
from psycopg.types.json import Json  # Ensure JSON compatibility

class Battle(BaseModel):
    attacker_id: str
    defender_id: str
    planet_id: str
    battle_log: dict

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

router = APIRouter()

@router.post("/")
def create_battle(battle: Battle):
    conn = connect_to_db()
    if conn:
        battle_id = str(uuid4())
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO battles (id, attacker_id, defender_id, planet_id, battle_log) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id;
            """, (battle_id, battle.attacker_id, battle.defender_id, battle.planet_id, Json(battle.battle_log)))
            conn.commit()
        conn.close()
        return {"id": battle_id, "attacker_id": battle.attacker_id, "defender_id": battle.defender_id}
    raise HTTPException(status_code=500, detail="Error creating battle.")

@router.get("/{battle_id}")
def read_battle(battle_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM battles WHERE id = %s", (battle_id,))
            battle = cursor.fetchone()
        conn.close()
        if battle:
            return {
                "id": battle[0],
                "attacker_id": battle[1],
                "defender_id": battle[2],
                "planet_id": battle[3],
                "battle_log": battle[4]
            }
    raise HTTPException(status_code=404, detail="Battle not found.")

@router.get("/")
def read_all_battles():
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM battles")
            battles = cursor.fetchall()
        conn.close()
        return [
            {
                "id": battle[0],
                "attacker_id": battle[1],
                "defender_id": battle[2],
                "planet_id": battle[3],
                "battle_log": battle[4]
            } for battle in battles
        ]
    raise HTTPException(status_code=500, detail="Error fetching battles.")

@router.put("/{battle_id}")
def update_battle(battle_id: str, battle: Battle):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE battles 
                SET attacker_id = %s, defender_id = %s, planet_id = %s, battle_log = %s 
                WHERE id = %s
            """, (battle.attacker_id, battle.defender_id, battle.planet_id, Json(battle.battle_log), battle_id))
            conn.commit()
        conn.close()
        return {"message": "Battle updated successfully."}
    raise HTTPException(status_code=500, detail="Error updating battle.")

@router.delete("/{battle_id}")
def delete_battle(battle_id: str):
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM battles WHERE id = %s", (battle_id,))
            conn.commit()
        conn.close()
        return {"message": "Battle deleted successfully."}
    raise HTTPException(status_code=500, detail="Error deleting battle.")

from fastapi import APIRouter, HTTPException, Depends
import psycopg
from pydantic import BaseModel
from uuid import uuid4
import json
from auth.endpoints import get_current_user
from database.database import connect_to_db

class Battle(BaseModel):
    attacker_id: str
    defender_id: str
    planet_id: str
    battle_log: dict

router = APIRouter()

@router.post("/")
def create_battle(battle: Battle, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    battle_id = str(uuid4())
    battle_log_json = json.dumps(battle.battle_log)

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO battles (id, attacker_id, defender_id, planet_id, battle_log) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id;
            """, (battle_id, battle.attacker_id, battle.defender_id, battle.planet_id, battle_log_json))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating battle: {str(e)}")
    finally:
        conn.close()

    return {"id": battle_id, "attacker_id": battle.attacker_id, "defender_id": battle.defender_id}

@router.get("/{battle_id}")
def read_battle(battle_id: str, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, attacker_id, defender_id, planet_id, battle_log FROM battles WHERE id = %s", (battle_id,))
            battle = cursor.fetchone()
    finally:
        conn.close()

    if battle:
        return {
            "id": battle[0],
            "attacker_id": battle[1],
            "defender_id": battle[2],
            "planet_id": battle[3],
            "battle_log": json.loads(battle[4])
        }

    raise HTTPException(status_code=404, detail="Battle not found")

@router.get("/")
def read_all_battles(current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, attacker_id, defender_id, planet_id, battle_log FROM battles")
            battles = cursor.fetchall()
    finally:
        conn.close()

    return [
        {
            "id": battle[0],
            "attacker_id": battle[1],
            "defender_id": battle[2],
            "planet_id": battle[3],
            "battle_log": json.loads(battle[4])
        } for battle in battles
    ]

@router.put("/{battle_id}")
def update_battle(battle_id: str, battle: Battle, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    battle_log_json = json.dumps(battle.battle_log)

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT attacker_id FROM battles WHERE id = %s", (battle_id,))
            existing_battle = cursor.fetchone()
            if not existing_battle:
                raise HTTPException(status_code=404, detail="Battle not found")
            if existing_battle[0] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Unauthorized to update this battle")

            cursor.execute("""
                UPDATE battles 
                SET attacker_id = %s, defender_id = %s, planet_id = %s, battle_log = %s 
                WHERE id = %s
            """, (battle.attacker_id, battle.defender_id, battle.planet_id, battle_log_json, battle_id))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating battle: {str(e)}")
    finally:
        conn.close()

    return {"message": "Battle updated successfully"}

@router.delete("/{battle_id}")
def delete_battle(battle_id: str, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT attacker_id FROM battles WHERE id = %s", (battle_id,))
            existing_battle = cursor.fetchone()
            if not existing_battle:
                raise HTTPException(status_code=404, detail="Battle not found")
            if existing_battle[0] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Unauthorized to delete this battle")

            cursor.execute("DELETE FROM battles WHERE id = %s", (battle_id,))
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting battle: {str(e)}")
    finally:
        conn.close()

    return {"message": "Battle deleted successfully"}

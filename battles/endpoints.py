from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import json
from uuid import uuid4, UUID
from auth.endpoints import get_current_user
from database.database import connect_to_db

router = APIRouter()


class BattleRequest(BaseModel):
    attacker_fleet_id: str
    defender_fleet_id: str
    battle_type: str
    planet_id: str
    winner: str = None


class BattleOutcome(BaseModel):
    battle_id: str
    winner: str
    loser: str
    battle_report: dict


@router.post("/")
def create_battle(battle_request: BattleRequest, current_user: dict = Depends(get_current_user)):
    print("📦 Received battle creation request.")

    try:
        attacker_uuid = UUID(battle_request.attacker_fleet_id)
        defender_uuid = UUID(battle_request.defender_fleet_id)
        planet_uuid = UUID(battle_request.planet_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format in fleet or planet ID")

    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    battle_id = str(uuid4())
    print(f"⚔️ Creating battle with ID: {battle_id}")

    try:
        with conn.cursor() as cursor:
            print("🔍 Verifying attacker fleet ownership...")
            cursor.execute("SELECT user_id FROM user_fleets WHERE id = %s", (attacker_uuid,))
            attacker_fleet = cursor.fetchone()
            if not attacker_fleet or attacker_fleet[0] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Unauthorized or attacker fleet not found")

            print("🔍 Verifying defender fleet exists...")
            cursor.execute("SELECT user_id FROM user_fleets WHERE id = %s", (defender_uuid,))
            defender_fleet = cursor.fetchone()
            if not defender_fleet:
                raise HTTPException(status_code=404, detail="Defender fleet not found")

            print("📥 Inserting battle into database...")
            cursor.execute("""
                INSERT INTO battles (id, attacker_fleet_id, defender_fleet_id, battle_type, planet_id)
                VALUES (%s, %s, %s, %s, %s) RETURNING id;
            """, (battle_id, attacker_uuid, defender_uuid, battle_request.battle_type, planet_uuid))
            conn.commit()
            print(f"✅ Battle created successfully with ID: {battle_id}")
    except Exception as e:
        print(f"❌ Error during battle creation: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating battle: {str(e)}")
    finally:
        conn.close()

    return {
        "battle_id": battle_id,
        "attacker_fleet_id": str(attacker_uuid),
        "defender_fleet_id": str(defender_uuid),
        "battle_type": battle_request.battle_type,
        "planet_id": str(planet_uuid)
    }


@router.get("/{battle_id}")
def get_battle(battle_id: str, current_user: dict = Depends(get_current_user)):
    print(f"🔍 Fetching battle with ID: {battle_id}")
    try:
        battle_uuid = UUID(battle_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid battle ID format")

    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, attacker_fleet_id, defender_fleet_id, battle_type, planet_id, winner
                FROM battles WHERE id = %s
            """, (battle_uuid,))
            battle = cursor.fetchone()
    finally:
        conn.close()

    if battle:
        print("✅ Battle found.")
        return {
            "id": str(battle[0]),
            "attacker_fleet_id": str(battle[1]),
            "defender_fleet_id": str(battle[2]),
            "battle_type": battle[3],
            "planet_id": str(battle[4]),
            "winner": battle[5]
        }

    raise HTTPException(status_code=404, detail="Battle not found")


@router.put("/{battle_id}/outcome")
def set_battle_outcome(battle_id: str, battle_outcome: BattleOutcome, current_user: dict = Depends(get_current_user)):
    print(f"🧠 Setting outcome for battle ID: {battle_id}")
    try:
        battle_uuid = UUID(battle_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid battle ID format")

    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT attacker_fleet_id, defender_fleet_id FROM battles WHERE id = %s", (battle_uuid,))
            battle = cursor.fetchone()
            if not battle:
                raise HTTPException(status_code=404, detail="Battle not found")

            # Check if the user owns either fleet
            cursor.execute("SELECT user_id FROM user_fleets WHERE id = %s OR id = %s",
                           (battle[0], battle[1]))
            fleet_owners = cursor.fetchall()
            if not any(owner[0] == current_user["id"] for owner in fleet_owners):
                raise HTTPException(status_code=403, detail="Unauthorized to set battle outcome")

            print("✍️ Updating battle outcome...")
            cursor.execute("""
                UPDATE battles SET winner = %s WHERE id = %s
            """, (battle_outcome.winner, battle_uuid))

            print("📥 Inserting battle report...")
            cursor.execute("""
                INSERT INTO battle_reports (battle_id, winner, loser, report)
                VALUES (%s, %s, %s, %s)
            """, (
                battle_uuid,
                battle_outcome.winner,
                battle_outcome.loser,
                json.dumps(battle_outcome.battle_report)
            ))

            conn.commit()
            print("✅ Battle outcome saved.")
    except Exception as e:
        print(f"❌ Error saving battle outcome: {e}")
        raise HTTPException(status_code=500, detail=f"Error setting battle outcome: {str(e)}")
    finally:
        conn.close()

    return {"message": "Battle outcome set successfully"}


@router.get("/reports")
def get_battle_reports(current_user: dict = Depends(get_current_user)):
    print(f"📄 Fetching battle reports for user {current_user['id']}")
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            print("🔍 Fetching user's fleet IDs...")
            cursor.execute("SELECT id FROM user_fleets WHERE user_id = %s", (current_user["id"],))
            fleet_ids = [str(row[0]) for row in cursor.fetchall()]

            if not fleet_ids:
                print("❌ No fleets found for user.")
                return []

            print("🔍 Fetching reports for user's fleets...")
            cursor.execute("""
                SELECT battle_id, winner, loser, report 
                FROM battle_reports 
                WHERE battle_id IN (
                    SELECT id FROM battles 
                    WHERE attacker_fleet_id = ANY(%s) OR defender_fleet_id = ANY(%s)
                )
            """, (fleet_ids, fleet_ids))
            reports = cursor.fetchall()
    finally:
        conn.close()

    print(f"📦 Found {len(reports)} reports")
    return [
        {
            "battle_id": str(r[0]),
            "winner": r[1],
            "loser": r[2],
            "battle_report": json.loads(r[3])
        } for r in reports
    ]

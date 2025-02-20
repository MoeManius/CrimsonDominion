import os
import psycopg
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg.connect(DATABASE_URL)
    cursor = conn.cursor()
    print("Connected to the database successfully")
except Exception as e:
    print(f"Database connection failed: {e}")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Crimson Dominion server is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

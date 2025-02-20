from fastapi import FastAPI
from users.endpoints import router as users_router

app = FastAPI()

app.include_router(users_router, prefix="/users", tags=["users"])

@app.get("/")
def read_root():
    return {"message": "Welcome to CrimsonDominion API!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
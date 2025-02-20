from fastapi import FastAPI
from users.endpoints import router as users_router
from planets.endpoints import router as planets_router

app = FastAPI()

# Include Routers
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(planets_router, prefix="/planets", tags=["planets"])

@app.get("/")
def root():
    return {"message": "Welcome to the Crimson Dominion API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from users.endpoints import router as users_router
from planets.endpoints import router as planets_router
from buildings.endpoints import router as buildings_router
from user_buildings.endpoints import router as user_buildings_router
from battles.endpoints import router as battles_router
from user_fleets.endpoints import router as user_fleets_router
from auth.endpoints import router as auth_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(planets_router, prefix="/planets", tags=["Planets"])
app.include_router(buildings_router, prefix="/buildings", tags=["Buildings"])
app.include_router(user_buildings_router, prefix="/user_buildings", tags=["User Buildings"])
app.include_router(battles_router, prefix="/battles", tags=["Battles"])
app.include_router(user_fleets_router, prefix="/user_fleets", tags=["User Fleets"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

@app.get("/")
def read_root():
    return {"message": "Welcome to CrimsonDominion API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
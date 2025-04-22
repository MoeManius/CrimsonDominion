from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import routers
from auth.endpoints import router as auth_router
from users.endpoints import router as users_router
from buildings.endpoints import router as buildings_router
from user_buildings.endpoints import router as user_buildings_router
from user_fleets.endpoints import router as user_fleets_router
from battles.endpoints import router as battles_router

# Add the planets router import
from planets.endpoints import router as planets_router

# -----------------------
# Logging Setup
# -----------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# -----------------------
# FastAPI App Setup
# -----------------------
app = FastAPI(
    title="🚀 CRIMSON DOMINION API",
    description="""
Welcome to the **Crimson Dominion API** — the backend powering your intergalactic empire!

With this API, you can:
- 👨‍🚀 Manage Users & Admins
- 🏗️ Construct & Level Up Buildings
- 🛸 Build & Customize Fleets
- 🌍 Own Planets & Colonize New Ones
- ⚔️ Engage in Strategic Battles

**Authentication:**  
Every request requires JWT-based access.  
Use `/auth/login` to obtain your `access_token` & `refresh_token`.

Built for speed. Designed for domination. 👑
    """,
    version="1.0.0",
    contact={
        "name": "CrimsonDominion Dev",
        "url": "https://TheCrimsonDominion.com",
        "email": "Moe.Yassir@gmail.com",
    },
    license_info={
        "name": "OpenSource / MIT",
    }
)

# -----------------------
# CORS Middleware
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Include All Routers
# -----------------------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(buildings_router, prefix="/buildings", tags=["Buildings"])
app.include_router(user_buildings_router, prefix="/user-buildings", tags=["User Buildings"])
app.include_router(user_fleets_router, prefix="/user-fleets", tags=["User Fleets"])
app.include_router(battles_router, prefix="/battles", tags=["Battles"])

# Include the planets router
app.include_router(planets_router, prefix="/planets", tags=["Planets"])

# -----------------------
# Startup Event
# -----------------------
@app.on_event("startup")
def startup():
    logger.info("🚀 Crimson Dominion API has launched.")

# -----------------------
# Root Endpoint
# -----------------------
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Crimson Dominion API — Rule the stars!"}

# -----------------------
# Run with Uvicorn
# -----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

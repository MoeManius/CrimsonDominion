# **Crimson Dominion - Backend API**  
A FastAPI-based backend for **Crimson Dominion**, a strategic space empire game. This backend provides **authentication, user management, planets, battles, buildings, and more**.  

## **📝 Features**  
✅ User authentication with **JWT** (Signup, Login, Logout, /me)  
✅ Password encryption using **bcrypt**  
✅ Role-based access control (Coming soon)  
✅ Manage **users, planets, buildings, battles**  
✅ PostgreSQL as the database  
✅ Organized **modular API structure**  

---

## **📌 Technologies Used**  
- **FastAPI** 🚀 - For building the API  
- **PostgreSQL** 🛢️ - For database storage  
- **psycopg** 🔗 - For connecting to the database  
- **bcrypt** 🔐 - For secure password hashing  
- **PyJWT** 🔑 - For handling authentication tokens  
- **dotenv** 📦 - For managing environment variables  

---

## **🚀Setup Instructions**  

### **1️⃣ Clone the Repository**
```sh
git clone https://github.com/your-repo/crimson-dominion-api.git
cd crimson-dominion-api

2️⃣ Install Dependencies
Make sure you have Python 3.10+ installed, then run:
pip install -r requirements.txt

3️⃣ Set Up the Environment Variables
Create a .env file in the project root and add:

DATABASE_URL=postgresql://postgres:MuschelSuppe1409@localhost/CrimsonDominion
SECRET_KEY="EXAMPLE KEY"
REFRESH_SECRET_KEY="EXAMPLE KEY"
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

4️⃣ Set Up the Database
Run the following SQL script in PostgreSQL:

-- Create the users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create the planets table
CREATE TABLE planets (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    owner_id UUID REFERENCES users(id) DEFAULT NULL,
    resources JSON NOT NULL DEFAULT '{}',
    discovered_at TIMESTAMP DEFAULT NULL,
    claimed_at TIMESTAMP DEFAULT NULL
);

-- Create the buildings table
CREATE TABLE buildings (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type ENUM('Metal Mine', 'Fusion Reactor', 'Dyson Sphere', 'Crystal Mine', 'Synthesizer', 'Dock') NOT NULL,
    resource_cost JSON NOT NULL
);

-- Create the user_buildings table (many-to-many relation between users and buildings)
CREATE TABLE user_buildings (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    planet_id UUID REFERENCES planets(id),
    building_id UUID REFERENCES buildings(id),
    level INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create the user_fleets table
CREATE TABLE user_fleets (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    planet_id UUID REFERENCES planets(id) DEFAULT NULL,
    status ENUM('Idle', 'Exploring', 'Claiming', 'Defending', 'Attacking', 'Returning') NOT NULL DEFAULT 'Idle',
    ships JSON NOT NULL,
    target_planet UUID REFERENCES planets(id) DEFAULT NULL,
    departure_time TIMESTAMP DEFAULT NULL,
    arrival_time TIMESTAMP DEFAULT NULL
);

-- Create the battles table
CREATE TABLE battles (
    id UUID PRIMARY KEY,
    attacker_id UUID REFERENCES users(id),
    defender_id UUID REFERENCES users(id),
    planet_id UUID REFERENCES planets(id),
    attacker_fleet JSON NOT NULL,
    defender_fleet JSON NOT NULL,
    outcome ENUM('Attacker Won', 'Defender Won', 'Draw') NOT NULL,
    battle_time TIMESTAMP DEFAULT NOW()
);

-- Add index for better performance on commonly queried columns
CREATE INDEX idx_planets_owner_id ON planets(owner_id);
CREATE INDEX idx_user_buildings_user_id ON user_buildings(user_id);
CREATE INDEX idx_user_fleets_user_id ON user_fleets(user_id);
CREATE INDEX idx_battles_attacker_id ON battles(attacker_id);
CREATE INDEX idx_battles_defender_id ON battles(defender_id);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS username VARCHAR(50) UNIQUE NOT NULL;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email VARCHAR(100) UNIQUE NOT NULL;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS password_hash TEXT NOT NULL;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;


5️⃣ Run the Server
uvicorn app.main:app --reload
The API will be available at http://127.0.0.1:8000 🚀

🛠️ Usage
You can test the API using Postman or cURL.
Alternatively, visit the interactive API docs:

    Swagger UI: http://127.0.0.1:8000/docs
    ReDoc: http://127.0.0.1:8000/redoc

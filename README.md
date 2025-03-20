# **Crimson Dominion - Backend API**  MVP COMPLETION STATUS: 70% ETA: 30.03.2025
🚀 A FastAPI-based backend for **Crimson Dominion**, a strategic space empire game. This backend provides **authentication, user management, planets, battles, buildings, and more**.  

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

## **🚀 Setup Instructions**  

### **1️⃣ Clone the Repository**
```sh
git clone https://github.com/your-repo/crimson-dominion-api.git
cd crimson-dominion-api

2️⃣ Install Dependencies
Make sure you have Python 3.10+ installed, then run:
pip install -r requirements.txt

3️⃣ Set Up the Environment Variables
Create a .env file in the project root and add:

DATABASE_URL=postgresql://postgres:yourpassword@localhost/CrimsonDominion
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60

4️⃣ Set Up the Database
Run the following SQL script in PostgreSQL:

CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

(Repeat for planets, buildings, battles, etc.)

5️⃣ Run the Server
uvicorn app.main:app --reload
The API will be available at http://127.0.0.1:8000 🚀

🛠️ Usage
You can test the API using Postman or cURL.
Alternatively, visit the interactive API docs:

    Swagger UI: http://127.0.0.1:8000/docs
    ReDoc: http://127.0.0.1:8000/redoc

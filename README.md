# 🎯 Mission Impossible Escape Room

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red)
![SQLite](https://img.shields.io/badge/Database-SQLite-green)


An interactive **multi-room escape room web application** inspired by the *Mission Impossible* universe.

Players progress through a sequence of technical and logic-based challenges including **signal analysis, anomaly detection, and cryptographic puzzles**, while the backend tracks their progress and enforces the mission flow.

The project demonstrates **backend-driven game logic, state persistence, and modular room architecture**.

## Live Demo

Play the game here:

https://your-render-url

---

# 🕹 Gameplay Overview

The player acts as an **IMF agent** tasked with neutralizing a rogue AI entity.

Mission flow:

1️⃣ Authentication with codename and passphrase  
2️⃣ Prelude challenge (security identification)  
3️⃣ Room-based puzzles with increasing difficulty  
4️⃣ Backend-verified success conditions  
5️⃣ Final mission summary

Each room introduces a different mechanic, and progression is enforced server-side (players can only access the next room after the previous room is marked as succeeded in the database).

Example challenges:

• signal classification  
• anomaly detection  
• RSA cryptography puzzle  
• LIDAR-style scanning interface  

---

# 🧠 Key Features

• Multi-room mission architecture  
• Backend-controlled player progression  
• Persistent game state using SQLite  
• Modular room implementation using Flask blueprints  
• Interactive JavaScript puzzle interfaces  
• RSA cryptography challenge with optional C++ acceleration  
• Progress tracking with completion timestamps  
• Mission summary dashboard  

---

# 🏗 Architecture

The project follows a **backend-driven architecture** where the Flask server controls mission logic while the frontend provides the interactive interface.

```
Client (Browser)
        │
        ▼
Flask Application
        │
        ├── Game Logic
        ├── Player Authentication
        ├── Room Progress Control
        └── API endpoints for puzzles
        │
        ▼
SQLite Database
        │
        └── Player progress persistence
```

---

# 🧰 Tech Stack

Backend  
• Python  
• Flask  
• Flask-SQLAlchemy  
• SQLite  

Frontend  
• HTML  
• CSS  
• JavaScript  

Computation  
• NumPy  
• Optional C++ extension via pybind11  

---

# 📂 Project Structure

```
backend/
  server.py
  config.py
  db.py
  models.py
  progress.py
  rooms/
  templates/
  static/
  instance/

cpp/
  rsa_module.cpp

frontend/

tests/

build/

rsa_cpp.cp310-win_amd64.pyd

requirements.txt
setup.py
Dockerfile
docker-compose.yml
.dockerignore
.env.example
.gitignore
```

---

# 🚀 Run Locally

Create virtual environment

```
python -m venv .venv
```

Activate

Windows

```
.venv\Scripts\activate
```

macOS / Linux

```
source .venv/bin/activate
```

Install dependencies

```
pip install -r requirements.txt
```

Run server

```
python -m backend.server
```

Open browser

```
http://127.0.0.1:5000
```

Note: Ensure the `backend/instance/` folder exists before first run. SQLite cannot create the database file if the directory is missing.

The SQLite database file (`game.db`) is created automatically in `backend/instance/` on first run.

---

## Running Tests

This project includes an automated test suite using pytest.

Install dependencies and run the tests:

```
python -m pip install -r requirements.txt
python -m pytest
```

Notes:
- Tests run using pytest.
- A temporary SQLite database is used during testing.
- The local game database is not modified.

Example success output:

```
24 passed in 2.34s
```

---

# ⚙ Environment Variables

Create `.env` from `.env.example`

Example:

```
SECRET_KEY=change-me-in-production
DATABASE_URL=sqlite:///backend/instance/game.db
FLASK_ENV=development
PORT=5000
```

---

# 🐳 Run with Docker

```
docker-compose up --build
```

Open:

```
http://localhost:5000
```

---

## Game Mechanics

Each room introduces a different technical challenge:

Room 1  
Pattern recognition puzzle. The player selects the correct images from a small set; the backend validates the exact match to mark success.

Room 2  
Signal classification using NumPy. The player labels submarine vs. non-submarine images; the server computes a Bayesian success score and enforces minimum correct coverage before unlocking the next room.

Room 3  
Anomaly detection challenge. The player submits a flight path trajectory; the server scores curvature and jerk to detect anomalies and unlocks the next room when the score exceeds a threshold.

Room 4  
RSA decryption puzzle combining Python and optional C++ acceleration. The player chooses a candidate RSA key; the backend decrypts a hidden message and checks for specific plaintext tokens before marking mission complete.

Each room includes a **My Progress** link so the player can view their current stats during the mission, not only at the end.

Progress tracking stores per-room start time, success time, and attempt count to generate the mission summary.

---

## Game Progression / Backend Logic

Progression is enforced server-side: each room must be marked as succeeded in the database before the next room is accessible.

The backend stores per-room start time, success time, and attempt count, and exposes the **My Progress** summary during the game.

---

# 🖼 Screenshots

*(Add screenshots here to demonstrate gameplay)*

Examples to include:

• login screen  
• puzzle interface  
• LIDAR scanning panel  
• RSA challenge  
• mission summary page  

---

# 📊 Learning Goals

This project was developed to practice:

• backend architecture design  
• stateful web applications  
• integrating computational puzzles into web systems  
• designing modular game mechanics  
• combining Python and C++ for performance-sensitive logic  

---

# 📝 Notes

Local SQLite database files are excluded from Git.

Room 4 includes a **Python fallback implementation** if the optional C++ RSA module cannot be compiled.

The C++ RSA module is optional. This repository includes a precompiled `rsa_cpp.cp310-win_amd64.pyd` built for Python 3.10 on Windows, but the game runs normally without it on other Python versions.

For production deployments, using **PostgreSQL instead of SQLite** is recommended.

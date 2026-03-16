# 💣 Mission Impossible Escape Room

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red)
![SQLite](https://img.shields.io/badge/Database-SQLite-green)


An interactive **multi-room escape room web application** inspired by the *Mission Impossible* universe.

Players progress through a sequence of technical and logic-based challenges including **signal analysis, anomaly detection, and cryptographic puzzles**, while the backend tracks their progress and enforces the mission flow.

The project demonstrates **backend-driven game logic, state persistence, and modular room architecture**.

## 🧨 Live Demo

Play the game here:

https://mission-impossible-escape-room.onrender.com

<img width="1890" height="825" alt="image" src="https://github.com/user-attachments/assets/04b1c22b-9ce0-4bb6-9038-21fc755c46c7" />

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

<img width="1393" height="888" alt="image" src="https://github.com/user-attachments/assets/92900546-2fef-42d9-868a-fcc8cdad1b69" />
<img width="1432" height="895" alt="image" src="https://github.com/user-attachments/assets/b884bd0a-9fb0-4ab6-a56b-2f2b67640e3e" />

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

## 💥 Game Mechanics

Each room introduces a different technical challenge:

Room 1 - Pattern Recognition
Pattern recognition puzzle. The player selects the correct images from a small set; the backend validates the exact match to mark success.

<img width="1862" height="902" alt="image" src="https://github.com/user-attachments/assets/ca6590f5-e505-46fe-925b-d2e8afeca9b3" />

Room 2 - Signal Classification
Signal classification using NumPy. The player labels submarine vs. non-submarine images; the server computes a Bayesian success score and enforces minimum correct coverage before unlocking the next room.

<img width="1522" height="890" alt="image" src="https://github.com/user-attachments/assets/7ba5fb65-f425-41f8-bee1-92b9f3793091" />

Room 3 - Anomaly Detection
Anomaly detection challenge. The player submits a flight path trajectory; the server scores curvature and jerk to detect anomalies and unlocks the next room when the score exceeds a threshold.

<img width="1846" height="880" alt="image" src="https://github.com/user-attachments/assets/56e4d90c-3548-424c-8a1a-b2ad58c49297" />

Room 4 - RSA Decryption
RSA decryption puzzle combining Python and optional C++ acceleration. The player chooses a candidate RSA key; the backend decrypts a hidden message and checks for specific plaintext tokens before marking mission complete.

<img width="1817" height="870" alt="image" src="https://github.com/user-attachments/assets/34f18c86-e8fa-446f-8de8-cca920c6e11e" />
<img width="1817" height="712" alt="image" src="https://github.com/user-attachments/assets/5cd2cfdf-f9aa-4536-a71d-1f8414ab482e" />

Each room includes a **My Progress** link so the player can view their current stats during the mission, not only at the end.

Progress tracking stores per-room start time, success time, and attempt count to generate the mission summary.

---

## 🏁 Mission Summary

<img width="1191" height="796" alt="image" src="https://github.com/user-attachments/assets/494bfcc4-3686-483f-9cd4-5dc44605109b" />
<img width="1147" height="498" alt="image" src="https://github.com/user-attachments/assets/9746f456-5478-4533-abdc-772b40ddbacb" />

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

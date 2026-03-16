import sqlite3

# Connect to the local SQLite database
conn = sqlite3.connect("backend/instance/game.db")
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

# Example: fetch all users
try:
    cursor.execute("SELECT * FROM users;")
    print("Users:", cursor.fetchall())
except Exception as e:
    print("No 'users' table yet or error:", e)

conn.close()

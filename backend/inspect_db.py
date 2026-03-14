import sqlite3

# להתחבר ל-DB
conn = sqlite3.connect("backend/instance/game.db")
cursor = conn.cursor()

# לראות את כל הטבלאות
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

# לדוגמה: לשלוף את כל המשתמשים
try:
    cursor.execute("SELECT * FROM users;")
    print("Users:", cursor.fetchall())
except Exception as e:
    print("No 'users' table yet or error:", e)

conn.close()

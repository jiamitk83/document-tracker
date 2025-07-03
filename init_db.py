import sqlite3
import os

# Ensure correct path
db_path = os.path.join(os.path.dirname(__file__), 'database.db')

# Create new DB file
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
''')

# Documents table with stage and all required fields
cursor.execute('''
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    stage TEXT DEFAULT 'submitted',
    teacher_feedback TEXT,
    coordinator_feedback TEXT,
    principal_feedback TEXT,
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()

print("✅ Database and tables created successfully.")

import sqlite3

# Replace with the correct path to your database
conn = sqlite3.connect(r'C:\Users\91750\PycharmProjects\Document tracker new\document_tracker\database.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE documents ADD COLUMN stage TEXT DEFAULT 'Submitted'")
    conn.commit()
    print("✅ 'stage' column added successfully.")
except sqlite3.OperationalError as e:
    print("❌ Error:", e)

conn.close()

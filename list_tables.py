import sqlite3

conn = sqlite3.connect(r'C:\Users\91750\PycharmProjects\Document tracker new\document_tracker\database.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("📋 Tables in database:", tables)

conn.close()

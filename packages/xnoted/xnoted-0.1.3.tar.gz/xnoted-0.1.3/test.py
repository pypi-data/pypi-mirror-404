import sqlite3

DB_NAME = "database.db"
con = sqlite3.connect(DB_NAME)
cur = con.cursor()

# List all tables in the database
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()

print("Tables in the database:")
for table in tables:
    print(f"  - {table[0]}")

con.close()

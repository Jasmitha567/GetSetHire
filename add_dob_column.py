# add_dob_column.py
import sqlite3
import os

# Ensure instance directory exists
os.makedirs('instance', exist_ok=True)

# Connect to database
conn = sqlite3.connect('instance/job_ready.db')
cursor = conn.cursor()

try:
    # Add DOB column
    cursor.execute("ALTER TABLE users ADD COLUMN dob TEXT")
    print("✅ Added DOB column to users table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ️ DOB column already exists")
    else:
        print(f"Error: {e}")
except Exception as e:
    print(f"Error: {e}")

conn.commit()
conn.close()
print("Database update complete!")

import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('instance/job_ready.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                resume_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                skills TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                company TEXT,
                readiness_score INTEGER,
                lacking_skills TEXT,
                roadmap TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        self.conn.commit()
    
    def create_user(self, name, email, password):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, email):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cursor.fetchone()
    
    def get_user_by_id(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()
    
    def store_user_skills(self, user_id, skills):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO user_skills (user_id, skills) VALUES (?, ?)",
            (user_id, json.dumps(skills))
        )
        self.conn.commit()
    
    def get_user_skills(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT skills FROM user_skills WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else []
    
    def update_resume_path(self, user_id, path):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET resume_path = ? WHERE id = ?",
            (path, user_id)
        )
        self.conn.commit()
    
    def store_analysis(self, user_id, role, company, readiness_score, lacking_skills, roadmap):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO analysis_results 
               (user_id, role, company, readiness_score, lacking_skills, roadmap) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, role, company, readiness_score, 
             json.dumps(lacking_skills), json.dumps(roadmap))
        )
        self.conn.commit()
    
    def get_latest_analysis(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM analysis_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        result = cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'role': result[2],
                'company': result[3],
                'readiness_score': result[4],
                'lacking_skills': json.loads(result[5]),
                'roadmap': json.loads(result[6]),
                'created_at': result[7]
            }
        return None
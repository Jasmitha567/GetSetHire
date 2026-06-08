# fix_tasks.py
import sqlite3
import json

conn = sqlite3.connect('instance/job_ready.db')
cursor = conn.cursor()

# Get all analyses
cursor.execute("SELECT id, user_id, lacking_skills FROM analysis_results")
analyses = cursor.fetchall()

for analysis_id, user_id, lacking_skills_str in analyses:
    lacking_skills = json.loads(lacking_skills_str)
    
    # Delete existing tasks
    cursor.execute("DELETE FROM progress_tasks WHERE analysis_id = ?", (analysis_id,))
    
    # Create new tasks
    for skill in lacking_skills:
        tasks = [
            f"Complete a course on {skill.title()}",
            f"Practice {skill.title()} with hands-on projects",
            f"Review {skill.title()} interview questions"
        ]
        for task in tasks:
            cursor.execute("""INSERT INTO progress_tasks 
                              (user_id, analysis_id, skill, task, completed) 
                              VALUES (?, ?, ?, ?, 0)""",
                          (user_id, analysis_id, skill, task))
    
    print(f"Created tasks for analysis {analysis_id}: {len(lacking_skills)} skills")

conn.commit()
conn.close()
print("Done!")
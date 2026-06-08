# debug_youtube.py
import sqlite3
import json

conn = sqlite3.connect('instance/job_ready.db')
cursor = conn.cursor()

cursor.execute("SELECT id, role, roadmap FROM analysis_results ORDER BY id DESC LIMIT 5")
analyses = cursor.fetchall()

print("\n" + "="*60)
print("YouTube URLs in Database:")
print("="*60)

for analysis_id, role, roadmap_str in analyses:
    print(f"\nAnalysis {analysis_id}: {role}")
    try:
        roadmap = json.loads(roadmap_str)
        if 'learning_resources' in roadmap:
            for skill, resources in roadmap['learning_resources'].items():
                youtube_url = resources.get('youtube_url', 'NOT FOUND')
                print(f"  {skill}: {youtube_url[:80]}...")
        else:
            print("  No learning_resources found")
    except Exception as e:
        print(f"  Error parsing: {e}")

conn.close()
# fix_existing_youtube_urls.py
import sqlite3
import json
from ai_service import ai_service

conn = sqlite3.connect('instance/job_ready.db')
cursor = conn.cursor()

# Get all analyses
cursor.execute("SELECT id, user_id, lacking_skills, roadmap FROM analysis_results")
analyses = cursor.fetchall()

print("Fixing YouTube URLs for existing analyses...")
print("="*60)

for analysis_id, user_id, lacking_skills_str, roadmap_str in analyses:
    try:
        lacking_skills = json.loads(lacking_skills_str)
        roadmap = json.loads(roadmap_str)
        
        # Fix learning_resources
        if 'learning_resources' not in roadmap:
            roadmap['learning_resources'] = {}
        
        fixed_count = 0
        for skill in lacking_skills:
            # Get correct YouTube URL
            correct_url = ai_service.get_youtube_url(skill)
            video_id = ''
            if 'youtube.com/watch?v=' in correct_url:
                video_id = correct_url.split('v=')[-1].split('&')[0]
            
            # Update or create resource
            if skill not in roadmap['learning_resources']:
                roadmap['learning_resources'][skill] = {}
            
            roadmap['learning_resources'][skill]['youtube_url'] = correct_url
            roadmap['learning_resources'][skill]['youtube_video_id'] = video_id
            
            if 'courses' not in roadmap['learning_resources'][skill]:
                roadmap['learning_resources'][skill]['courses'] = [
                    f"Udemy: Complete {skill.title()} Bootcamp",
                    f"Coursera: {skill.title()} Specialization"
                ]
            if 'practice' not in roadmap['learning_resources'][skill]:
                roadmap['learning_resources'][skill]['practice'] = [
                    f"Build a project using {skill.title()}",
                    f"Complete practice problems on {skill.title()}"
                ]
            
            fixed_count += 1
            print(f"  Fixed {skill}: {correct_url[:60]}...")
        
        # Save back to database
        cursor.execute("""UPDATE analysis_results 
                         SET roadmap = ?
                         WHERE id = ?""",
                      (json.dumps(roadmap), analysis_id))
        
        print(f"✅ Analysis {analysis_id}: Fixed {fixed_count} skills")
        
    except Exception as e:
        print(f"❌ Error fixing analysis {analysis_id}: {e}")

conn.commit()
conn.close()
print("\n" + "="*60)
print("✅ All analyses fixed! Run python app.py to see changes.")
from ai_service import ai_service
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import os
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime
import hashlib
import re
from resume_parser import ResumeParser
from naukri_scraper import NaukriScraper

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-2024-make-it-very-secure'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

CORS(app)

# Initialize scraper
scraper = NaukriScraper()

# Database helper functions
def get_db():
    os.makedirs('instance', exist_ok=True)
    conn = sqlite3.connect('instance/job_ready.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  resume_path TEXT,
                  dob TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_skills
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  skills TEXT,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS analysis_results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  role TEXT,
                  company TEXT,
                  readiness_score INTEGER,
                  lacking_skills TEXT,
                  roadmap TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS progress_tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  analysis_id INTEGER,
                  skill TEXT,
                  task TEXT,
                  completed INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (analysis_id) REFERENCES analysis_results (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS progress_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  analysis_id INTEGER,
                  date DATE,
                  hours_studied INTEGER,
                  tasks_completed INTEGER,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (analysis_id) REFERENCES analysis_results (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS video_progress
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  skill TEXT,
                  progress INTEGER DEFAULT 0,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  UNIQUE(user_id, skill))''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(name, email, password, dob=None):
    try:
        conn = get_db()
        c = conn.cursor()
        hashed_pw = hash_password(password)
        c.execute("INSERT INTO users (name, email, password, dob) VALUES (?, ?, ?, ?)",
                 (name, email, hashed_pw, dob))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        return None

def get_user_by_email(email):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def verify_user(email, password):
    user = get_user_by_email(email)
    if user and user['password'] == hash_password(password):
        return user
    return None

def store_user_skills(user_id, skills):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM user_skills WHERE user_id = ?", (user_id,))
    c.execute("INSERT INTO user_skills (user_id, skills) VALUES (?, ?)",
             (user_id, json.dumps(skills)))
    conn.commit()
    conn.close()

def get_user_skills(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT skills FROM user_skills WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1", (user_id,))
    result = c.fetchone()
    conn.close()
    return json.loads(result['skills']) if result else []

def update_resume_path(user_id, path):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET resume_path = ? WHERE id = ?", (path, user_id))
    conn.commit()
    conn.close()

def store_analysis(user_id, role, company, readiness_score, lacking_skills, roadmap):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO analysis_results 
                 (user_id, role, company, readiness_score, lacking_skills, roadmap) 
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (user_id, role, company, readiness_score, 
               json.dumps(lacking_skills), json.dumps(roadmap)))
    conn.commit()
    analysis_id = c.lastrowid
    conn.close()
    return analysis_id

def get_latest_analysis(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT * FROM analysis_results 
                 WHERE user_id = ? ORDER BY created_at DESC LIMIT 1""", (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return {
            'id': result['id'],
            'role': result['role'],
            'company': result['company'],
            'readiness_score': result['readiness_score'],
            'lacking_skills': json.loads(result['lacking_skills']),
            'roadmap': json.loads(result['roadmap'])
        }
    return None

def get_all_analyses(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT id, role, company, readiness_score, created_at 
                 FROM analysis_results 
                 WHERE user_id = ? 
                 ORDER BY created_at DESC""", (user_id,))
    results = c.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_analysis_by_id(analysis_id, user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT * FROM analysis_results 
                 WHERE id = ? AND user_id = ?""", (analysis_id, user_id))
    result = c.fetchone()
    conn.close()
    if result:
        return {
            'id': result['id'],
            'role': result['role'],
            'company': result['company'],
            'readiness_score': result['readiness_score'],
            'lacking_skills': json.loads(result['lacking_skills']),
            'roadmap': json.loads(result['roadmap']),
            'created_at': result['created_at']
        }
    return None

def create_tasks_for_analysis(user_id, analysis_id, lacking_skills):
    """Create checklist tasks for each missing skill"""
    conn = get_db()
    c = conn.cursor()
    
    # First delete any existing tasks for this analysis
    c.execute("DELETE FROM progress_tasks WHERE analysis_id = ? AND user_id = ?", 
              (analysis_id, user_id))
    
    # Create new tasks
    for skill in lacking_skills:
        tasks = [
            f"Complete a course on {skill.title()}",
            f"Practice {skill.title()} with hands-on projects",
            f"Review {skill.title()} interview questions"
        ]
        for task in tasks:
            c.execute("""INSERT INTO progress_tasks 
                         (user_id, analysis_id, skill, task, completed) 
                         VALUES (?, ?, ?, ?, 0)""",
                      (user_id, analysis_id, skill, task))
    
    conn.commit()
    conn.close()
    print(f"✅ Created {len(lacking_skills) * 3} tasks for analysis {analysis_id}")

def get_tasks_for_analysis(analysis_id, user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT * FROM progress_tasks 
                 WHERE user_id = ? AND analysis_id = ? 
                 ORDER BY skill""", (user_id, analysis_id))
    tasks = c.fetchall()
    conn.close()
    return [{'id': t['id'], 'skill': t['skill'], 'task': t['task'], 'completed': t['completed']} for t in tasks]

def update_task_status(task_id, completed):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE progress_tasks SET completed = ? WHERE id = ?", (completed, task_id))
    conn.commit()
    conn.close()

def get_updated_readiness_score(analysis_id, user_id):
    """Calculate updated readiness score based on completed tasks"""
    conn = get_db()
    c = conn.cursor()
    
    # Get the analysis
    c.execute("SELECT lacking_skills, readiness_score FROM analysis_results WHERE id = ? AND user_id = ?", 
              (analysis_id, user_id))
    result = c.fetchone()
    
    if not result:
        return 0
    
    lacking_skills = json.loads(result['lacking_skills'])
    original_score = result['readiness_score']
    
    # Get completed tasks
    c.execute("SELECT DISTINCT skill FROM progress_tasks WHERE user_id = ? AND analysis_id = ? AND completed = 1", 
              (user_id, analysis_id))
    completed_tasks = c.fetchall()
    completed_skills = set([task['skill'] for task in completed_tasks])
    
    conn.close()
    
    # Calculate new score based on completed skills (not just tasks)
    if len(lacking_skills) > 0:
        # Each completed skill gives equal weight
        skills_completed = len([s for s in lacking_skills if s in completed_skills])
        # Score = original_score + improvement based on completed skills
        # Max improvement = 100 - original_score
        max_improvement = 100 - original_score
        improvement = (skills_completed / len(lacking_skills)) * max_improvement
        new_score = min(100, original_score + improvement)
        return int(new_score)
    
    return original_score

def normalize_skill(skill):
    skill_lower = skill.lower().strip()
    if skill_lower in ['c', 'c language']:
        return 'c'
    if skill_lower in ['c++', 'cpp']:
        return 'c++'
    if skill_lower in ['oracle sql', 'mysql', 'postgresql', 'sqlite', 'oracle']:
        return 'sql'
    if skill_lower in ['object oriented', 'oop', 'object-oriented']:
        return 'oop'
    if skill_lower in ['ui', 'ux', 'ui/ux']:
        return 'ui/ux'
    if skill_lower in ['figma']:
        return 'figma'
    if skill_lower in ['design thinking']:
        return 'design thinking'
    if skill_lower in ['analytical thinking', 'problem solving']:
        return 'problem solving'
    if skill_lower in ['communication']:
        return 'communication'
    return skill_lower

def get_fallback_requirements(role, company):
    fallback_db = {
        'Software Engineer': ['Python', 'Java', 'SQL', 'Data Structures', 'Algorithms', 'OOP', 'Problem Solving', 'Git', 'Communication'],
        'Data Scientist': ['Python', 'SQL', 'Machine Learning', 'Statistics', 'Pandas', 'Data Visualization', 'Communication'],
        'Frontend Developer': ['JavaScript', 'React', 'HTML5', 'CSS3', 'TypeScript', 'UI/UX', 'Responsive Design', 'Git'],
        'Backend Developer': ['Python', 'Java', 'SQL', 'REST APIs', 'Microservices', 'OOP', 'Git', 'Communication'],
        'DevOps Engineer': ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Linux', 'Python', 'Jenkins'],
        'Full Stack Developer': ['JavaScript', 'React', 'Node.js', 'Python', 'SQL', 'REST APIs', 'Git', 'Communication']
    }
    return fallback_db.get(role, ['Python', 'JavaScript', 'SQL', 'Communication', 'Problem Solving'])

def generate_dynamic_roadmap(missing_skills, total_weeks, weekly_hours=10):
    num_skills = len(missing_skills)
    
    if total_weeks >= num_skills * 2:
        confidence_level = "High - You have plenty of time!"
    elif total_weeks >= num_skills:
        confidence_level = "Medium - Stay consistent"
    else:
        confidence_level = "Challenging - Need more time or hours"
    
    if num_skills == 0:
        weekly_plan = []
        for week in range(1, min(total_weeks + 1, 13)):
            weekly_plan.append({
                'week': week,
                'skills': ['Interview Preparation', 'Advanced Concepts'],
                'tasks': [
                    "Review core concepts daily",
                    "Solve 2-3 LeetCode problems",
                    "Practice system design questions",
                    "Mock interview with peer",
                    "Update portfolio/GitHub"
                ],
                'milestone': f"Week {week}: Interview Ready"
            })
        return {
            'total_weeks': total_weeks,
            'recommended_hours_per_week': weekly_hours,
            'weekly_plan': weekly_plan[:total_weeks],
            'learning_resources': {},
            'study_strategy': f'Focus on interview preparation. Study {weekly_hours} hours/week.',
            'skills_to_master': 0,
            'confidence_level': confidence_level
        }
    
    skills_per_week = max(1, min(2, (num_skills + total_weeks - 1) // total_weeks))
    weekly_plan = []
    skill_index = 0
    
    for week in range(1, total_weeks + 1):
        if skill_index >= num_skills:
            week_skills = ['Review & Practice', 'Interview Prep']
            tasks = [
                "Review all learned skills",
                "Build a capstone project",
                "Practice mock interviews",
                "Update resume with new skills"
            ]
            milestone = f"Week {week}: Mastery & Interview Preparation"
        else:
            end_idx = min(skill_index + skills_per_week, num_skills)
            week_skills = missing_skills[skill_index:end_idx]
            skill_index = end_idx
            tasks = []
            for skill in week_skills:
                tasks.extend([
                    f"Complete a course on {skill.title()}",
                    f"Practice {skill.title()} with hands-on projects",
                    f"Build a mini-project using {skill.title()}"
                ])
            tasks = tasks[:4]
            milestone = f"Week {week}: Master {', '.join(week_skills)}"
        
        weekly_plan.append({
            'week': week,
            'skills': week_skills,
            'tasks': tasks,
            'milestone': milestone
        })
    
    learning_resources = {}
    for skill in missing_skills[:6]:
        learning_resources[skill] = {
            'courses': [f"Udemy: {skill.title()} Bootcamp", f"Coursera: {skill.title()} Specialization"],
            'practice': [f"LeetCode: {skill.title()} Problems", f"Build a project using {skill.title()}"]
        }
    
    return {
        'total_weeks': total_weeks,
        'recommended_hours_per_week': weekly_hours,
        'weekly_plan': weekly_plan,
        'learning_resources': learning_resources,
        'study_strategy': f"Study {weekly_hours} hours/week. Master {num_skills} skill(s).",
        'skills_to_master': len(missing_skills),
        'confidence_level': confidence_level
    }

def get_matched_skills_for_analysis(analysis, user_id):
    user_skills = get_user_skills(user_id)
    required_skills = get_fallback_requirements(analysis['role'], analysis['company'])
    
    user_skills_normalized = [normalize_skill(s) for s in user_skills]
    required_skills_normalized = [normalize_skill(s) for s in required_skills]
    
    matched = []
    for req_skill in required_skills_normalized:
        for user_skill in user_skills_normalized:
            if req_skill == user_skill or req_skill in user_skill or user_skill in req_skill:
                matched.append(req_skill)
                break
    
    matched = list(set(matched))
    return matched

def calculate_readiness_score(matched_skills, lacking_skills):
    total_skills = len(matched_skills) + len(lacking_skills)
    if total_skills > 0:
        score = int((len(matched_skills) / total_skills) * 100)
    else:
        score = 0
    return score

# Initialize database
init_db()

# ============= ROUTES =============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        user = verify_user(email, password)
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        dob = request.form.get('dob', '').strip()
        
        if not name or not email or not password:
            return render_template('signup.html', error='All fields are required')
        
        import re
        if len(password) < 8:
            return render_template('signup.html', error='Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', password):
            return render_template('signup.html', error='Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', password):
            return render_template('signup.html', error='Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', password):
            return render_template('signup.html', error='Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return render_template('signup.html', error='Password must contain at least one special character')
        
        if dob:
            from datetime import datetime
            try:
                birth_date = datetime.strptime(dob, '%Y-%m-%d')
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                if age < 8:
                    return render_template('signup.html', error='Minimum requirement not satisfied')
            except:
                return render_template('signup.html', error='Minimum requirement not satisfied')
        else:
            return render_template('signup.html', error='Minimum requirement not satisfied')
        
        user_id = create_user(name, email, password, dob)
        
        if user_id:
            session.clear()
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_email'] = email
            return redirect(url_for('dashboard'))
        else:
            return render_template('signup.html', error='Email already exists')
    
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    analyses = get_all_analyses(session['user_id'])
    
    for analysis in analyses:
        # Get dynamic score from tasks (for dashboard progress bar)
        analysis['dynamic_score'] = get_updated_readiness_score(analysis['id'], session['user_id'])
        
        # Also calculate matched skills for display
        matched_skills = get_matched_skills_for_analysis(analysis, session['user_id'])
        analysis['matched_skills_count'] = len(matched_skills)
        
        # Calculate total skills
        lacking_skills = analysis.get('lacking_skills', [])
        if isinstance(lacking_skills, str):
            lacking_skills = json.loads(lacking_skills)
        analysis['total_skills'] = len(matched_skills) + len(lacking_skills)
    
    skills = get_user_skills(session['user_id'])
    
    return render_template('dashboard.html', 
                         user=session.get('user_name', 'User'),
                         analyses=analyses,
                         skills_count=len(skills))

@app.route('/upload', methods=['GET', 'POST'])
def upload_resume():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'resume' not in request.files:
            return render_template('upload.html', error='No file uploaded')
        file = request.files['resume']
        if file.filename == '':
            return render_template('upload.html', error='No file selected')
        if file:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            filename = secure_filename(f"{session['user_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            parser = ResumeParser(filepath)
            skills = parser.extract_skills()
            print(f"Extracted skills: {skills}")
            store_user_skills(session['user_id'], skills)
            update_resume_path(session['user_id'], filepath)
            session['skills_uploaded'] = True
            session['skills'] = skills
            return redirect(url_for('choose_path'))
    return render_template('upload.html')

@app.route('/choose-path')
def choose_path():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('role_selection.html')

@app.route('/questionnaire')
def questionnaire():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('questionnaire.html')

@app.route('/analyze-questionnaire', methods=['POST'])
def analyze_questionnaire():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    answers = data.get('answers', [])
    role_scores = {
        'Software Engineer': 0, 'Frontend Developer': 0, 'Backend Developer': 0,
        'Data Scientist': 0, 'DevOps Engineer': 0, 'Full Stack Developer': 0
    }
    for answer in answers:
        answer_lower = answer.lower()
        if any(word in answer_lower for word in ['website', 'application', 'coding']):
            role_scores['Software Engineer'] += 2
            role_scores['Full Stack Developer'] += 2
        if any(word in answer_lower for word in ['data', 'analytics', 'statistics']):
            role_scores['Data Scientist'] += 3
        if any(word in answer_lower for word in ['infrastructure', 'cloud', 'server']):
            role_scores['DevOps Engineer'] += 3
        if any(word in answer_lower for word in ['design', 'interface', 'ui']):
            role_scores['Frontend Developer'] += 2
        if any(word in answer_lower for word in ['backend', 'api', 'database']):
            role_scores['Backend Developer'] += 2
    suggested_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    suggested_roles = [role for role, score in suggested_roles if score > 0]
    if not suggested_roles:
        suggested_roles = ['Software Engineer', 'Data Analyst', 'Frontend Developer']
    return jsonify({'roles': suggested_roles})

@app.route('/suggested-roles')
def suggested_roles():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('suggested_roles.html')

@app.route('/api/ai-analyze', methods=['POST'])
def ai_powered_analysis():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        target_role = data.get('role', 'Software Engineer')
        target_company = data.get('company', 'Google')
        
        user_skills = get_user_skills(session['user_id'])
        print(f"📋 User skills: {user_skills}")
        
        scraped_skills = scraper.get_job_requirements(target_role, target_company)
        using_fallback = False
        if scraped_skills and len(scraped_skills) >= 3:
            required_skills = scraped_skills
            source = 'real-time'
        else:
            required_skills = get_fallback_requirements(target_role, target_company)
            source = 'fallback'
            using_fallback = True
        
        print(f"📋 Required skills ({source}): {required_skills}")
        
        user_skills_normalized = [normalize_skill(s) for s in user_skills]
        required_skills_normalized = [normalize_skill(s) for s in required_skills]
        
        matched = []
        missing = []
        
        for req_skill in required_skills_normalized:
            found = False
            for user_skill in user_skills_normalized:
                if req_skill == user_skill or req_skill in user_skill or user_skill in req_skill:
                    matched.append(req_skill)
                    found = True
                    break
            if not found:
                missing.append(req_skill)
        
        matched = list(set(matched))
        missing = list(set(missing))
        
        total_skills = len(matched) + len(missing)
        readiness_score = int((len(matched) / total_skills) * 100) if total_skills > 0 else 0
        
        print(f"📊 Results - Matched: {matched} ({len(matched)}), Missing: {missing} ({len(missing)}), Score: {readiness_score}%")
        
        roadmap = generate_dynamic_roadmap(missing, 12, 10)
        
        analysis_id = store_analysis(session['user_id'], target_role, target_company, 
                                    readiness_score, missing, roadmap)
        create_tasks_for_analysis(session['user_id'], analysis_id, missing)
        
        return jsonify({
            'success': True,
            'readiness_score': readiness_score,
            'matched_skills': matched,
            'lacking_skills': missing,
            'analysis_id': analysis_id,
            'source': source,
            'using_fallback': using_fallback,
            'fallback_message': 'Using cached job requirements (real-time scrape temporarily unavailable)' if using_fallback else None,
            'ai_enhanced': True
        })
        
    except Exception as e:
        print(f"❌ Error in AI analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/generate-roadmap', methods=['POST'])
def generate_roadmap():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        analysis_id = data.get('analysis_id')
        target_role = data.get('role')
        target_company = data.get('company')
        weeks = int(data.get('weeks', 12))
        weekly_hours = int(data.get('weekly_hours', 10))
        matched_skills = data.get('matched_skills', [])
        missing_skills = data.get('missing_skills', [])
        
        print(f"🎯 Generating AI roadmap for: {target_role}")
        print(f"📋 Missing skills: {missing_skills}")
        print(f"⏰ Weeks: {weeks}, Weekly hours: {weekly_hours}")
        
        total_skills = len(matched_skills) + len(missing_skills)
        readiness_score = int((len(matched_skills) / total_skills) * 100) if total_skills > 0 else 0
        
        # FORCE create learning_resources with correct YouTube URLs
        learning_resources = {}
        for skill in missing_skills:
            # Get the correct YouTube URL from ai_service
            youtube_url = ai_service.get_youtube_url(skill)
            video_id = ''
            if 'youtube.com/watch?v=' in youtube_url:
                video_id = youtube_url.split('v=')[-1].split('&')[0]
            elif 'youtu.be/' in youtube_url:
                video_id = youtube_url.split('youtu.be/')[-1].split('?')[0]
            
            learning_resources[skill] = {
                "courses": [
                    f"Udemy: Complete {skill.title()} Bootcamp",
                    f"Coursera: {skill.title()} Specialization"
                ],
                "youtube_url": youtube_url,
                "youtube_video_id": video_id,
                "practice": [
                    f"Build a project using {skill.title()}",
                    f"Complete practice problems on {skill.title()}"
                ]
            }
            print(f"  📺 {skill}: {youtube_url}")
        
        # Try AI first
        roadmap = None
        ai_used = False
        
        if missing_skills and len(missing_skills) > 0:
            print("🤖 Generating AI-powered roadmap...")
            preparation_days = weeks * 7
            
            ai_roadmap = ai_service.generate_personalized_roadmap(
                missing_skills, target_role, preparation_days, weekly_hours
            )
            
            if ai_roadmap:
                try:
                    parsed_roadmap = json.loads(ai_roadmap)
                    if parsed_roadmap and 'weekly_plan' in parsed_roadmap and len(parsed_roadmap['weekly_plan']) > 0:
                        roadmap = parsed_roadmap
                        ai_used = True
                        print(f"✅ AI roadmap generated with {len(roadmap['weekly_plan'])} weeks!")
                    else:
                        print("⚠️ AI response invalid - missing weekly_plan")
                        roadmap = None
                except json.JSONDecodeError as e:
                    print(f"⚠️ AI JSON parse error: {e}")
                    roadmap = None
            else:
                print("⚠️ AI returned None")
        
        # Use fallback if AI failed
        if not roadmap:
            print("📝 Using fallback roadmap")
            roadmap = generate_dynamic_roadmap(missing_skills, weeks, weekly_hours)
            ai_used = False
        
        # FORCE OVERRIDE learning_resources with correct URLs
        roadmap['learning_resources'] = learning_resources
        
        # Store the roadmap in database
        conn = get_db()
        c = conn.cursor()
        c.execute("""UPDATE analysis_results 
                     SET readiness_score = ?, lacking_skills = ?, roadmap = ?
                     WHERE id = ? AND user_id = ?""",
                  (readiness_score, json.dumps(missing_skills), json.dumps(roadmap), 
                   analysis_id, session['user_id']))
        conn.commit()
        conn.close()
        
        # Delete old tasks
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM progress_tasks WHERE analysis_id = ? AND user_id = ?", 
                  (analysis_id, session['user_id']))
        conn.commit()
        conn.close()
        
        # Create new tasks from weekly plan
        for week in roadmap.get('weekly_plan', []):
            for skill in week.get('skills', []):
                for task in week.get('tasks', [])[:4]:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""INSERT INTO progress_tasks 
                                 (user_id, analysis_id, skill, task, completed) 
                                 VALUES (?, ?, ?, ?, 0)""",
                              (session['user_id'], analysis_id, skill, task))
                    conn.commit()
                    conn.close()
        
        print(f"✅ Roadmap saved with {len(learning_resources)} skills and YouTube URLs")
        
        return jsonify({
            'success': True,
            'readiness_score': readiness_score,
            'roadmap': roadmap,
            'ai_generated': ai_used
        })
        
    except Exception as e:
        print(f"❌ Error generating roadmap: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    analysis = get_latest_analysis(session['user_id'])
    if not analysis:
        return redirect(url_for('choose_path'))
    
    matched_skills = get_matched_skills_for_analysis(analysis, session['user_id'])
    lacking_skills = analysis['lacking_skills']
    readiness_score = calculate_readiness_score(matched_skills, lacking_skills)
    
    analysis['matched_skills'] = matched_skills
    analysis['readiness_score'] = readiness_score
    
    return render_template('results.html', analysis=analysis)

@app.route('/results/<int:analysis_id>')
def results_by_id(analysis_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    analysis = get_analysis_by_id(analysis_id, session['user_id'])
    if not analysis:
        return redirect(url_for('dashboard'))
    
    matched_skills = get_matched_skills_for_analysis(analysis, session['user_id'])
    lacking_skills = analysis['lacking_skills']
    readiness_score = calculate_readiness_score(matched_skills, lacking_skills)
    
    analysis['matched_skills'] = matched_skills
    analysis['readiness_score'] = readiness_score
    
    return render_template('results.html', analysis=analysis)

@app.route('/roadmap')
def roadmap():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    analysis = get_latest_analysis(session['user_id'])
    if not analysis:
        return redirect(url_for('choose_path'))
    
    return render_template('roadmap.html', analysis=analysis)

@app.route('/tracking/<int:analysis_id>')
def tracking(analysis_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    analysis = get_analysis_by_id(analysis_id, session['user_id'])
    if not analysis:
        return redirect(url_for('dashboard'))
    tasks = get_tasks_for_analysis(analysis_id, session['user_id'])
    
    # Debug: Print YouTube URLs
    print("\n" + "="*50)
    print("TRACKING PAGE - YouTube URLs Debug:")
    if 'roadmap' in analysis and 'learning_resources' in analysis['roadmap']:
        for skill, resources in analysis['roadmap']['learning_resources'].items():
            youtube_url = resources.get('youtube_url', 'NOT FOUND')
            print(f"  {skill}: {youtube_url}")
    else:
        print("  No learning_resources found in roadmap")
    print("="*50 + "\n")
    
    return render_template('tracking.html', analysis=analysis, tasks=tasks)
@app.route('/update_task', methods=['POST'])
def update_task():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    task_id = data.get('task_id')
    completed = data.get('completed')
    update_task_status(task_id, completed)
    return jsonify({'success': True})

@app.route('/api/update-video-progress', methods=['POST'])
def update_video_progress():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    skill = data.get('skill')
    progress = data.get('progress')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO video_progress (user_id, skill, progress) 
                 VALUES (?, ?, ?)
                 ON CONFLICT(user_id, skill) 
                 DO UPDATE SET progress = ?, updated_at = CURRENT_TIMESTAMP""",
              (session['user_id'], skill, progress, progress))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/get-video-progress', methods=['GET'])
def get_video_progress():
    """Get video progress for a skill"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    skill = request.args.get('skill', '')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT progress FROM video_progress WHERE user_id = ? AND skill = ?", 
              (session['user_id'], skill))
    result = c.fetchone()
    conn.close()
    
    return jsonify({'progress': result['progress'] if result else 0})

@app.route('/watch-video')
def watch_video():
    """Embedded YouTube video player with progress tracking"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    skill = request.args.get('skill', '')
    video_id = request.args.get('video_id', '')
    title = request.args.get('title', skill + ' Tutorial')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT progress FROM video_progress WHERE user_id = ? AND skill = ?", 
              (session['user_id'], skill))
    result = c.fetchone()
    conn.close()
    
    progress = result['progress'] if result else 0
    
    return render_template('video_tracker.html', 
                         video_id=video_id, 
                         skill_name=skill, 
                         skill_title=title,
                         progress=progress)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/manage-skills')
def manage_skills():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    skills = get_user_skills(session['user_id'])
    return render_template('manage_skills.html', skills=skills)

@app.route('/api/skills', methods=['GET'])
def api_get_skills():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    skills = get_user_skills(session['user_id'])
    return jsonify({'skills': skills})

@app.route('/api/skills/add', methods=['POST'])
def api_add_skill():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    new_skill = data.get('skill', '').strip().lower()
    if not new_skill:
        return jsonify({'error': 'Skill name required'}), 400
    current_skills = get_user_skills(session['user_id'])
    if new_skill not in [s.lower() for s in current_skills]:
        current_skills.append(new_skill)
        store_user_skills(session['user_id'], current_skills)
        return jsonify({'success': True, 'skills': current_skills})
    else:
        return jsonify({'error': 'Skill already exists'}), 400

@app.route('/api/skills/remove', methods=['POST'])
def api_remove_skill():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    skill_to_remove = data.get('skill', '').strip().lower()
    if not skill_to_remove:
        return jsonify({'error': 'Skill name required'}), 400
    current_skills = get_user_skills(session['user_id'])
    updated_skills = [s for s in current_skills if s.lower() != skill_to_remove]
    if len(updated_skills) != len(current_skills):
        store_user_skills(session['user_id'], updated_skills)
        return jsonify({'success': True, 'skills': updated_skills})
    else:
        return jsonify({'error': 'Skill not found'}), 404

@app.route('/api/delete-analysis/<int:analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    """Delete a specific analysis and its related tasks"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute("DELETE FROM progress_tasks WHERE analysis_id = ? AND user_id = ?", 
                  (analysis_id, session['user_id']))
        c.execute("DELETE FROM analysis_results WHERE id = ? AND user_id = ?", 
                  (analysis_id, session['user_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Analysis deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting analysis: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/test-api', methods=['GET'])
def test_api():
    return jsonify({'status': 'ok', 'message': 'API is working'})

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('instance', exist_ok=True)
    app.run(debug=True)
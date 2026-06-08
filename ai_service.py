# ai_service.py
import os
import json
import re
import requests
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class GroqAIService:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("⚠️ WARNING: GROQ_API_KEY not found in .env file!")
            print("   Please add: GROQ_API_KEY=your_actual_api_key_here")
        else:
            print(f"✅ Groq API key loaded (starts with: {api_key[:15]}...)")
        
        self.client = Groq(api_key=api_key) if api_key else None
        self.models = {
            'fast': 'llama-3.1-8b-instant',
            'balanced': 'llama-3.3-70b-versatile',
        }
        self.model = self.models['balanced']
        
        # REAL working YouTube video URLs (fallback when API fails)
        self.real_youtube_urls = {
            'docker': 'https://www.youtube.com/watch?v=3c-iBn73dDE',
            'kubernetes': 'https://www.youtube.com/watch?v=s_o8dwzRlu4',
            'terraform': 'https://www.youtube.com/watch?v=SLB_c_ayRMo',
            'linux': 'https://www.youtube.com/watch?v=sWbUDqM-S10',
            'aws': 'https://www.youtube.com/watch?v=ulprqHHWlng',
            'git': 'https://www.youtube.com/watch?v=RGOj5yH7evk',
            'jenkins': 'https://www.youtube.com/watch?v=eB0nFw2E_xQ',
            'python': 'https://www.youtube.com/watch?v=_uQrJ0TkZlc',
            'javascript': 'https://www.youtube.com/watch?v=W6NZfCO5SIk',
            'react': 'https://www.youtube.com/watch?v=nTeuhbP7wdE',
            'sql': 'https://www.youtube.com/watch?v=HXV3zeQKqGY',
            'statistics': 'https://www.youtube.com/watch?v=xxpc-HPKN28',
            'data visualization': 'https://www.youtube.com/watch?v=5Zg-C8AAIGg',
            'tensorflow': 'https://www.youtube.com/watch?v=tPYj3fFJGjk',
            'machine learning': 'https://www.youtube.com/watch?v=Gv9_4yqtHFI',
        }
        
    def get_youtube_url(self, skill):
        skill_lower = skill.lower().strip()
        for key, url in self.real_youtube_urls.items():
            if key in skill_lower or skill_lower in key:
                return url
        return f"https://www.youtube.com/results?search_query={skill_lower.replace(' ', '+')}+tutorial"
    
    def check_internet(self):
        """Check if internet is available for Groq API"""
        try:
            requests.get("https://api.groq.com", timeout=5)
            return True
        except:
            return False
    
    def generate_personalized_roadmap(self, missing_skills, target_role, preparation_days, weekly_hours):
        """Generate roadmap - TRY Groq API first, fallback to template"""
        
        if not missing_skills:
            return None
            
        total_weeks = max(1, preparation_days // 7)
        skills_list = ', '.join(missing_skills)
        
        print(f"\n{'='*50}")
        print(f"🤖 Generating AI roadmap for: {skills_list}")
        print(f"🎯 Target Role: {target_role}")
        print(f"⏰ Total Weeks: {total_weeks}, Hours/Week: {weekly_hours}")
        print(f"{'='*50}")
        
        # FIRST: Try Groq API
        if self.client and self.check_internet():
            print("🌐 Internet detected - Attempting Groq API call...")
            
            # Build base learning resources
            learning_resources = {}
            for skill in missing_skills:
                youtube_url = self.get_youtube_url(skill)
                video_id = ''
                if 'youtube.com/watch?v=' in youtube_url:
                    video_id = youtube_url.split('v=')[-1].split('&')[0]
                
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
            
            # PROMPT for Groq API
            prompt = f"""You are an expert career coach and technical trainer. Create a DETAILED learning roadmap.

SKILLS TO LEARN: {skills_list}
TARGET JOB ROLE: {target_role}
TIME AVAILABLE: {total_weeks} weeks
STUDY HOURS PER WEEK: {weekly_hours} hours

Create a JSON roadmap with:
1. A weekly plan ({total_weeks} weeks total)
2. For EACH skill, provide 4-6 specific, actionable tasks (not generic)
3. Meaningful milestones
4. A study strategy tailored to these skills

Return ONLY valid JSON. No markdown, no explanations.

JSON STRUCTURE:
{{
    "total_weeks": {total_weeks},
    "recommended_hours_per_week": {weekly_hours},
    "weekly_plan": [
        {{
            "week": 1,
            "skills": ["skill_name"],
            "tasks": [
                "Specific task 1",
                "Specific task 2", 
                "Specific task 3",
                "Specific task 4"
            ],
            "milestone": "Clear weekly milestone"
        }}
    ],
    "study_strategy": "Detailed study strategy here",
    "skills_to_master": {len(missing_skills)},
    "confidence_level": "High"
}}

Make the tasks SPECIFIC and ACTIONABLE, not generic like "Watch tutorial". Include hands-on exercises, projects, and practical applications."""
            
            try:
                print("🚀 Calling Groq API (Llama 3.3 70B)...")
                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=0.7,
                    max_tokens=4096,
                    timeout=30
                )
                
                content = response.choices[0].message.content
                print(f"✅ Groq API responded: {len(content)} characters")
                
                # Clean up response
                content = content.strip()
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'```\s*$', '', content)
                content = re.sub(r'```\s*', '', content)
                
                # Extract JSON
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed = json.loads(json_str)
                    
                    # Add YouTube URLs to the response
                    parsed['learning_resources'] = learning_resources
                    
                    print(f"✅ Groq API SUCCESS! Generated {len(parsed.get('weekly_plan', []))} weeks")
                    return json.dumps(parsed)
                else:
                    print("⚠️ No JSON found in Groq response")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
            except Exception as e:
                print(f"❌ Groq API error: {e}")
        
        # FALLBACK: Use enhanced template (still good quality)
        print("📝 Groq API unavailable - Using enhanced template roadmap")
        return self._generate_enhanced_template(missing_skills, target_role, total_weeks, weekly_hours)
    
    def _generate_enhanced_template(self, missing_skills, target_role, total_weeks, weekly_hours):
        """Enhanced template with skill-specific tasks (when Groq API fails)"""
        
        # Build learning resources
        learning_resources = {}
        for skill in missing_skills:
            youtube_url = self.get_youtube_url(skill)
            video_id = ''
            if 'youtube.com/watch?v=' in youtube_url:
                video_id = youtube_url.split('v=')[-1].split('&')[0]
            
            learning_resources[skill] = {
                "courses": [
                    f"📺 {skill.title()} Full Course (YouTube)",
                    f"🎓 {skill.title()} Certification (Coursera)"
                ],
                "youtube_url": youtube_url,
                "youtube_video_id": video_id,
                "practice": [
                    f"💻 Build a real-world project with {skill.title()}",
                    f"🎯 Complete hands-on exercises"
                ]
            }
            print(f"  📺 {skill}: {youtube_url}")
        
        # Skill-specific task templates
        skill_tasks_map = {
            'docker': [
                "🐳 Learn Docker architecture (images, containers, registries)",
                "📦 Practice essential Docker commands: run, ps, exec, logs",
                "🔧 Create a Dockerfile for a sample application",
                "🌐 Build and run a multi-container app with Docker Compose"
            ],
            'kubernetes': [
                "☸️ Understand Kubernetes architecture (Pods, Services, Deployments)",
                "🎯 Learn kubectl commands: get, describe, apply, delete",
                "🔧 Create and deploy a simple Pod and Service",
                "📈 Practice scaling applications with ReplicaSets"
            ],
            'terraform': [
                "🏗️ Learn Infrastructure as Code concepts",
                "📝 Write your first Terraform configuration (HCL)",
                "🔧 Practice terraform init, plan, apply, destroy",
                "☁️ Provision cloud resources using Terraform"
            ],
            'linux': [
                "🐧 Master basic Linux commands: ls, cd, cp, mv, rm, grep",
                "🔐 Learn file permissions (chmod, chown) and user management",
                "📝 Practice text processing with sed, awk, vim",
                "🔄 Understand process management (ps, top, kill)"
            ],
            'statistics': [
                "📊 Learn descriptive statistics: mean, median, mode, std dev",
                "📈 Understand probability distributions",
                "🔬 Master hypothesis testing and p-values",
                "📉 Study correlation and regression analysis"
            ],
            'tensorflow': [
                "🧠 Understand TensorFlow basics and tensors",
                "🏗️ Build a simple neural network with Keras",
                "📊 Practice data preprocessing and augmentation",
                "🎯 Train and evaluate a classification model"
            ],
            'aws': [
                "☁️ Learn IAM: users, roles, policies, MFA",
                "💾 Master S3: buckets, versioning, lifecycle rules",
                "🖥️ Practice EC2: instances, security groups",
                "🗄️ Study RDS and DynamoDB basics"
            ]
        }
        
        # Create weekly plan
        weekly_plan = []
        weeks_per_skill = max(1, total_weeks // len(missing_skills)) if missing_skills else 1
        skill_index = 0
        
        for week in range(1, total_weeks + 1):
            if skill_index < len(missing_skills):
                current_skill = missing_skills[skill_index]
                skill_lower = current_skill.lower()
                
                # Get skill-specific tasks
                if skill_lower in skill_tasks_map:
                    tasks = skill_tasks_map[skill_lower]
                else:
                    tasks = [
                        f"📹 Watch: Complete {current_skill.title()} Tutorial",
                        f"💻 Practice: Hands-on {current_skill} exercises",
                        f"🏗️ Build: Mini project using {current_skill}",
                        f"📝 Review: Key concepts and take notes"
                    ]
                
                weekly_plan.append({
                    "week": week,
                    "skills": [current_skill],
                    "tasks": tasks,
                    "milestone": f"✅ Master fundamentals of {current_skill.title()}"
                })
                
                if week % weeks_per_skill == 0:
                    skill_index += 1
            else:
                weekly_plan.append({
                    "week": week,
                    "skills": ["Integration Project"],
                    "tasks": [
                        "🏗️ Build a capstone project combining all skills",
                        "🎯 Complete a real-world case study",
                        "🎤 Practice mock interviews on all topics",
                        "📊 Update your portfolio and GitHub"
                    ],
                    "milestone": f"🎉 Week {week}: Ready for interviews!"
                })
        
        roadmap = {
            "total_weeks": total_weeks,
            "recommended_hours_per_week": weekly_hours,
            "weekly_plan": weekly_plan,
            "learning_resources": learning_resources,
            "study_strategy": f"Study {weekly_hours} hours per week. Complete all hands-on projects. Practice daily.",
            "skills_to_master": len(missing_skills),
            "confidence_level": "High - Follow the structured plan!"
        }
        
        return json.dumps(roadmap)

ai_service = GroqAIService()
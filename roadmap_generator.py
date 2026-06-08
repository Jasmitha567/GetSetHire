import json
from datetime import datetime, timedelta
from typing import List, Dict

class RoadmapGenerator:
    def __init__(self):
        self.resources = {
            'python': {
                'courses': ['Python for Everybody (Coursera)', 'Complete Python Bootcamp (Udemy)'],
                'practice': ['LeetCode', 'HackerRank', 'CodeSignal'],
                'projects': ['Web scraper', 'API development', 'Data analysis script']
            },
            'java': {
                'courses': ['Java Programming Masterclass (Udemy)', 'Java Fundamentals (Pluralsight)'],
                'practice': ['LeetCode Java', 'CodeChef', 'GeeksforGeeks'],
                'projects': ['Spring Boot application', 'Android app', 'REST API']
            },
            'javascript': {
                'courses': ['The Complete JavaScript Course (Udemy)', 'JavaScript Algorithms (freeCodeCamp)'],
                'practice': ['CodeWars', 'LeetCode JavaScript', 'Frontend Mentor'],
                'projects': ['Interactive web app', 'Chrome extension', 'Game development']
            },
            'react': {
                'courses': ['React - The Complete Guide (Udemy)', 'Frontend Masters React'],
                'practice': ['React Challenges', 'Component building'],
                'projects': ['E-commerce frontend', 'Dashboard', 'Social media app']
            },
            'sql': {
                'courses': ['SQL for Data Science (Coursera)', 'The Complete SQL Bootcamp (Udemy)'],
                'practice': ['LeetCode SQL', 'HackerRank SQL', 'Mode Analytics'],
                'projects': ['Database design', 'Query optimization', 'Data analysis']
            },
            'aws': {
                'courses': ['AWS Certified Solutions Architect (Udemy)', 'AWS Training (Official)'],
                'practice': ['AWS Free Tier', 'Hands-on labs', 'Cloud practitioner'],
                'projects': ['Serverless app', 'Cloud migration', 'Infrastructure as code']
            }
        }
    
    def generate_roadmap(self, skill_gap: Dict, preparation_time_days: int) -> Dict:
        """Generate personalized learning roadmap"""
        lacking_skills = skill_gap.get('missing_skills', [])
        priorities = skill_gap.get('learning_priorities', [])
        
        # Calculate weekly schedule
        weeks = preparation_time_days // 7
        weekly_hours = 10  # Recommended weekly study hours
        total_hours = weeks * weekly_hours
        
        # Create weekly plan
        weekly_plan = []
        current_week = 1
        remaining_skills = priorities.copy()
        
        while remaining_skills and current_week <= weeks:
            week_skills = remaining_skills[:2]  # Focus on 2 skills per week
            remaining_skills = remaining_skills[2:]
            
            week_plan = {
                'week': current_week,
                'skills': week_skills,
                'tasks': self._create_weekly_tasks(week_skills),
                'milestones': self._create_milestones(current_week, week_skills)
            }
            weekly_plan.append(week_plan)
            current_week += 1
        
        # Generate month-by-month breakdown
        monthly_plan = self._create_monthly_plan(weekly_plan)
        
        # Generate project suggestions
        projects = self._suggest_projects(lacking_skills)
        
        # Generate interview prep schedule
        interview_prep = self._interview_preparation(weeks)
        
        return {
            'total_weeks': weeks,
            'recommended_hours_per_week': weekly_hours,
            'total_hours_needed': total_hours,
            'weekly_plan': weekly_plan,
            'monthly_plan': monthly_plan,
            'suggested_projects': projects,
            'interview_preparation': interview_prep,
            'learning_resources': self._get_resources(lacking_skills)
        }
    
    def _create_weekly_tasks(self, skills: List[Dict]) -> List[str]:
        """Create detailed weekly tasks"""
        tasks = []
        
        for skill_info in skills:
            skill = skill_info['skill'].lower()
            tasks.append(f"📚 Complete fundamental course on {skill_info['skill']}")
            tasks.append(f"💻 Practice {skill_info['skill']} on coding platforms")
            tasks.append(f"🏗️ Build a small project using {skill_info['skill']}")
            tasks.append(f"📝 Take assessment tests for {skill_info['skill']}")
        
        tasks.append("🎯 Review weekly progress and adjust plan if needed")
        tasks.append("📖 Read industry blogs and stay updated")
        
        return tasks
    
    def _create_milestones(self, week: int, skills: List[Dict]) -> List[str]:
        """Create weekly milestones"""
        milestones = []
        
        for skill in skills:
            milestones.append(f"✅ Master fundamentals of {skill['skill']}")
            milestones.append(f"🎯 Complete 5-10 exercises in {skill['skill']}")
        
        milestones.append(f"🏆 Complete week {week} learning objectives")
        
        return milestones
    
    def _create_monthly_plan(self, weekly_plan: List[Dict]) -> Dict:
        """Create monthly breakdown of learning"""
        months = {}
        current_month = 1
        month_weeks = []
        
        for plan in weekly_plan:
            month_weeks.append(plan)
            if len(month_weeks) == 4 or plan == weekly_plan[-1]:
                months[f"Month {current_month}"] = month_weeks
                current_month += 1
                month_weeks = []
        
        return months
    
    def _suggest_projects(self, skills: List[str]) -> List[Dict]:
        """Suggest projects based on skills to learn"""
        projects = []
        
        if any('web' in s.lower() or 'react' in s.lower() for s in skills):
            projects.append({
                'name': 'Portfolio Website',
                'description': 'Build a personal portfolio showcasing your skills and projects',
                'skills_used': ['HTML', 'CSS', 'JavaScript', 'React'],
                'timeline': '2 weeks'
            })
        
        if any('python' in s.lower() for s in skills):
            projects.append({
                'name': 'Job Search Dashboard',
                'description': 'Create a web app that tracks job applications and progress',
                'skills_used': ['Python', 'Flask/Django', 'SQL', 'REST API'],
                'timeline': '3 weeks'
            })
        
        if any('data' in s.lower() or 'machine' in s.lower() for s in skills):
            projects.append({
                'name': 'Skills Gap Analyzer',
                'description': 'Build a tool that analyzes resume skills against job requirements',
                'skills_used': ['Python', 'NLP', 'Machine Learning', 'Flask'],
                'timeline': '4 weeks'
            })
        
        return projects
    
    def _interview_preparation(self, weeks: int) -> Dict:
        """Generate interview preparation schedule"""
        return {
            'daily_practice': [
                'Solve 2-3 coding problems on LeetCode',
                'Review system design concepts',
                'Practice behavioral interview questions'
            ],
            'weekly_focus': [
                f'Week 1-{weeks//3}: Data Structures & Algorithms',
                f'Week {weeks//3+1}-{2*weeks//3}: System Design & Architecture',
                f'Week {2*weeks//3+1}-{weeks}: Mock Interviews & Company-specific prep'
            ],
            'resources': [
                'Cracking the Coding Interview book',
                'LeetCode Premium (recommended)',
                'System Design Interview by Alex Xu'
            ]
        }
    
    def _get_resources(self, skills: List[str]) -> Dict:
        """Get learning resources for skills"""
        resources = {}
        
        for skill in skills:
            skill_lower = skill.lower()
            found = False
            
            for key, value in self.resources.items():
                if key in skill_lower:
                    resources[skill] = value
                    found = True
                    break
            
            if not found:
                resources[skill] = {
                    'courses': ['Search for specialized courses on Coursera/Udemy'],
                    'practice': ['Practice platforms: LeetCode, HackerRank'],
                    'projects': ['Build projects applying this skill']
                }
        
        return resources

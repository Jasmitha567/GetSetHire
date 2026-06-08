import re
from typing import List, Dict, Set

class SkillAnalyzer:
    def __init__(self):
        self.skill_categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'go', 'rust'],
            'frontend': ['react', 'angular', 'vue', 'html', 'css', 'typescript'],
            'backend': ['node.js', 'express', 'django', 'flask', 'spring', 'asp.net'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
            'data_science': ['python', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn']
        }
    
    def analyze_gap(self, user_skills: List[str], job_requirements: Dict) -> Dict:
        """Analyze skill gap between user skills and job requirements"""
        required_skills = set(job_requirements.get('required_skills', []))
        user_skills_set = set([skill.lower() for skill in user_skills])
        
        # Find missing skills
        missing_skills = required_skills - user_skills_set
        
        # Find matched skills
        matched_skills = required_skills.intersection(user_skills_set)
        
        # Calculate readiness score (0-100)
        if len(required_skills) > 0:
            readiness_score = int((len(matched_skills) / len(required_skills)) * 100)
        else:
            readiness_score = 0
        
        # Categorize missing skills
        categorized_missing = self._categorize_skills(missing_skills)
        
        # Suggest learning priorities
        priorities = self._prioritize_skills(missing_skills, categorized_missing)
        
        return {
            'readiness_score': readiness_score,
            'matched_skills': list(matched_skills),
            'missing_skills': list(missing_skills),
            'categorized_missing': categorized_missing,
            'learning_priorities': priorities,
            'total_required': len(required_skills),
            'total_matched': len(matched_skills)
        }
    
    def _categorize_skills(self, skills: Set[str]) -> Dict:
        """Categorize skills into different areas"""
        categories = {
            'programming': [],
            'frontend': [],
            'backend': [],
            'database': [],
            'cloud': [],
            'data_science': [],
            'soft_skills': [],
            'other': []
        }
        
        for skill in skills:
            categorized = False
            for category, keywords in self.skill_categories.items():
                if any(keyword in skill.lower() for keyword in keywords):
                    categories[category].append(skill)
                    categorized = True
                    break
            
            if not categorized:
                # Check for soft skills
                soft_keywords = ['communication', 'team', 'leadership', 'problem solving', 'agile']
                if any(keyword in skill.lower() for keyword in soft_keywords):
                    categories['soft_skills'].append(skill)
                else:
                    categories['other'].append(skill)
        
        return {k: v for k, v in categories.items() if v}
    
    def _prioritize_skills(self, missing_skills: Set[str], categorized: Dict) -> List[Dict]:
        """Prioritize skills based on industry demand"""
        priorities = []
        
        # Define skill priority (higher number = higher priority)
        priority_weights = {
            'programming': 10,
            'cloud': 9,
            'database': 8,
            'backend': 8,
            'frontend': 7,
            'data_science': 7,
            'soft_skills': 6,
            'other': 5
        }
        
        for category, skills in categorized.items():
            weight = priority_weights.get(category, 5)
            for skill in skills:
                priorities.append({
                    'skill': skill,
                    'category': category,
                    'priority': weight,
                    'estimated_time': self._estimate_learning_time(skill)
                })
        
        # Sort by priority
        priorities.sort(key=lambda x: x['priority'], reverse=True)
        return priorities
    
    def _estimate_learning_time(self, skill: str) -> str:
        """Estimate learning time for a skill"""
        # Simple estimation based on skill complexity
        complex_skills = ['machine learning', 'deep learning', 'kubernetes', 'aws', 'system design']
        
        if any(cs in skill.lower() for cs in complex_skills):
            return "3-4 weeks"
        elif skill.lower() in ['python', 'javascript', 'sql', 'html', 'css']:
            return "1-2 weeks"
        else:
            return "2-3 weeks"
    
    def suggest_roles_from_questionnaire(self, answers: Dict) -> List[str]:
        """Suggest job roles based on questionnaire answers"""
        # Simple logic for demo - would be more sophisticated in production
        interests = answers.get('interests', '').lower()
        skills = answers.get('skills', '').lower()
        
        suggestions = []
        
        if 'coding' in interests or 'programming' in interests:
            if 'web' in interests or 'frontend' in skills:
                suggestions.append('Frontend Developer')
            if 'backend' in interests or 'database' in skills:
                suggestions.append('Backend Developer')
            suggestions.append('Software Engineer')
        
        if 'data' in interests or 'analysis' in interests:
            suggestions.append('Data Scientist')
            suggestions.append('Data Analyst')
        
        if 'cloud' in interests or 'devops' in interests:
            suggestions.append('DevOps Engineer')
        
        if not suggestions:
            suggestions = ['Software Engineer', 'Data Analyst', 'Frontend Developer']
        
        return suggestions[:3]  # Return top 3 suggestions

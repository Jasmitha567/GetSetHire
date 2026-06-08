import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json

class NaukriScraper:
    def __init__(self):
        # Set up Chrome options for headless scraping (runs in background)
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')  # Run in background
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        
    def get_job_requirements(self, role, company):
        """Scrape live job requirements from Naukri.com"""
        try:
            # Initialize driver
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
            
            # Search URL
            search_query = f"{role} {company}".replace(' ', '+')
            url = f"https://www.naukri.com/{search_query}-jobs"
            
            driver.get(url)
            time.sleep(random.uniform(3, 5))  # Wait for page to load
            
            # Find job listings
            jobs = driver.find_elements(By.CSS_SELECTOR, 'article.jobTuple, .jobCard, .jobTuple')
            
            if not jobs:
                return self._get_fallback_requirements(role)
            
            # Get first job posting
            first_job = jobs[0]
            first_job.click()
            time.sleep(2)
            
            # Switch to new window if opened
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[1])
            
            # Extract job description
            try:
                desc_elements = driver.find_elements(By.CSS_SELECTOR, '.job-description, .job-desc, .description')
                if desc_elements:
                    job_text = desc_elements[0].text.lower()
                else:
                    job_text = driver.page_source.lower()
            except:
                job_text = driver.page_source.lower()
            
            # Extract skills from job description
            skills = self._extract_skills_from_text(job_text)
            
            driver.quit()
            return skills
            
        except Exception as e:
            print(f"Scraping error: {e}")
            return self._get_fallback_requirements(role)
    
    def _extract_skills_from_text(self, text):
        """Extract technical skills from job description text"""
        skill_keywords = {
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
            'django', 'flask', 'spring', 'spring boot', 'sql', 'mongodb', 'postgresql',
            'mysql', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
            'git', 'ci/cd', 'devops', 'machine learning', 'deep learning', 'tensorflow',
            'pytorch', 'data science', 'analytics', 'tableau', 'power bi',
            'html', 'css', 'typescript', 'redux', 'graphql', 'rest api',
            'microservices', 'kafka', 'redis', 'elasticsearch', 'linux', 'unix',
            'c++', 'c#', '.net', 'php', 'ruby', 'swift', 'kotlin', 'flutter'
        }
        
        found_skills = set()
        for skill in skill_keywords:
            if skill in text:
                found_skills.add(skill)
        
        # Return top 8-10 skills
        return list(found_skills)[:10] if found_skills else []
    
    def _get_fallback_requirements(self, role):
        """Fallback requirements if scraping fails"""
        fallback = {
            'Software Engineer': ['Python', 'Java', 'SQL', 'Data Structures', 'Algorithms', 'System Design'],
            'Data Scientist': ['Python', 'SQL', 'Machine Learning', 'Statistics', 'TensorFlow', 'Data Visualization'],
            'Frontend Developer': ['JavaScript', 'React', 'HTML5', 'CSS3', 'TypeScript', 'Responsive Design'],
            'Backend Developer': ['Python', 'Java', 'SQL', 'REST APIs', 'Microservices', 'Database Design'],
            'DevOps Engineer': ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Linux', 'Terraform'],
            'Full Stack Developer': ['JavaScript', 'React', 'Node.js', 'Python', 'SQL', 'REST APIs'],
            'Machine Learning Engineer': ['Python', 'TensorFlow', 'PyTorch', 'Machine Learning', 'Deep Learning'],
            'Product Manager': ['Agile', 'Product Strategy', 'User Research', 'Data Analysis', 'Communication']
        }
        return fallback.get(role, ['Python', 'JavaScript', 'Communication', 'Problem Solving'])
import PyPDF2
import docx
import re
from typing import List, Set

class ResumeParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.skill_keywords = {
    # Programming languages
    'python', 'java', 'javascript', 'html', 'css', 'react', 'angular', 'vue',
    'node.js', 'express', 'django', 'flask', 'spring', 'sql', 'mongodb',
    'postgresql', 'mysql', 'git', 'docker', 'kubernetes', 'aws', 'azure',
    'machine learning', 'deep learning', 'nlp', 'tensorflow', 'pytorch',
    'data analysis', 'pandas', 'numpy', 'scikit-learn', 'tableau', 'power bi',
    'c++', 'c#', 'php', 'ruby', 'swift', 'kotlin', 'flutter', 'android',
    'ios', 'devops', 'ci/cd', 'jenkins', 'selenium', 'rest api', 'graphql',
    'agile', 'scrum', 'leadership', 'communication', 'problem solving',
    # Added for Jasmitha's resume
    'c', 'oop', 'object oriented', 'oracle sql', 'oracle', 'ui', 'ux',
    'figma', 'design thinking', 'testing', 'debugging', 'analytical thinking',
    'collaboration', 'attention to detail', 'computer networks', 'operating systems',
    'mysql', 'sql', 'python', 'c', 'ui/ux', 'user interface', 'user experience'
}
    
    def extract_text(self):
        text = ""
        if self.filepath.endswith('.pdf'):
            text = self._extract_from_pdf()
        elif self.filepath.endswith('.docx'):
            text = self._extract_from_docx()
        else:
            text = self._extract_from_txt()
        return text.lower()
    
    def _extract_from_pdf(self):
        text = ""
        try:
            with open(self.filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text
    
    def _extract_from_docx(self):
        text = ""
        try:
            doc = docx.Document(self.filepath)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error reading DOCX: {e}")
        return text
    
    def _extract_from_txt(self):
        text = ""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            print(f"Error reading TXT: {e}")
        return text
    
    def extract_skills(self) -> List[str]:
        text = self.extract_text()
        found_skills = set()
        
        # Pattern matching for skills
        for skill in self.skill_keywords:
            if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                found_skills.add(skill)
        
        # Extract from common sections
        sections = self._extract_sections(text)
        if 'skills' in sections:
            skill_section = sections['skills']
            for skill in self.skill_keywords:
                if skill in skill_section.lower():
                    found_skills.add(skill)
        
        return list(found_skills)
    
    def _extract_sections(self, text):
        sections = {}
        current_section = None
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Identify section headers
            if line.lower() in ['skills', 'technical skills', 'core competencies', 
                               'programming languages', 'technologies']:
                current_section = 'skills'
                sections[current_section] = []
            elif line.lower() in ['experience', 'work experience', 'employment']:
                current_section = 'experience'
                sections[current_section] = []
            elif line.lower() in ['education', 'academic background']:
                current_section = 'education'
                sections[current_section] = []
            
            if current_section and current_section in sections:
                sections[current_section].append(line)
        
        # Join section content
        for section in sections:
            sections[section] = ' '.join(sections[section])
        
        return sections

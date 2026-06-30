import re
from typing import List, Dict, Any
from pypdf import PdfReader 
from src.adapters.base_adapter import BaseAdapter


class PdfResumeAdapter(BaseAdapter):
    KNOWN_SKILLS = [
        "python", "java", "c++", "c#", "c", "javascript", "typescript", "go", "golang", 
        "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "dart", "shell", "bash",
        "html", "css", "react", "reactjs", "react.js", "angular", "vue", "vue.js", "next.js", 
        "nuxt.js", "svelte", "jquery", "tailwind", "tailwindcss", "bootstrap", "sass", "less",
        "node.js", "nodejs", "express", "express.js", "django", "flask", "fastapi", 
        "spring", "spring boot", "laravel", "rails", "ruby on rails", "asp.net", "nest.js",
        "flutter", "react native", "xamarin", "electron", "android studio",
        "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "sqlite", 
        "oracle", "microsoft sql server", "cassandra", "dynamodb", "neo4j", "elasticsearch",
        "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "keras", "pytorch", 
        "opencv", "nltk", "spacy", "huggingface", "llm", "langchain", "crewai",
        "power bi", "powerbi", "tableau", "excel", "sas", "looker",
        "spark", "apache spark", "hadoop", "snowflake", "bigquery", "databricks",
        "aws", "amazon web services", "azure", "gcp", "google cloud", "docker", 
        "kubernetes", "k8s", "jenkins", "github actions", "gitlab ci", "ansible", 
        "terraform", "linux", "nginx", "apache",
        "git", "github", "gitlab", "bitbucket", "jira", "confluence", "figma", 
        "postman", "graphql", "rest api", "soap", "grpc", "microservices", "agile", 
        "scrum", "ci/cd", "devops", "mlops", "streamlit", "gradio",
        "technical writing", "public speaking", "team leadership", "mentoring",
        "stakeholder management", "cross-functional collaboration", "negotiation",
        "client relations", "presentation skills", "agile project management",
        "verbal communication", "written communication", "interpersonal skills",
        "conflict resolution", "problem solving", "critical thinking", "time management",
        "active listening", "documentation", "teamwork"
    ]

    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error parsing PDF {file_path}: {e}")
            return []

        if not text.strip():
            return []

        # Comprehensive Regular Expressions
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]*)?\(?\d{3,5}\)?[-.\s]*\d{3,5}[-.\s]*\d{3,5}'
        generic_location_pattern = r'\b([A-Z][a-zA-Z\s]{1,20})[\s,\|/\-]{1,4}([A-Z][a-zA-Z\s]{1,20})\b'
        link_pattern = r'\b(?:https?://)?(?:www\.)?(?:linkedin\.com|github\.com|portfolio\-?\w*\.\w+)[^\s,]*\b'
        date_range_pattern = r'\b(\d{2}[-/]\d{2}[-/]\d{4}|\d{4}[-/]\d{2}|[A-Za-z]+\s+\d{4})\s*(?:\-|to)\s*(\d{2}[-/]\d{2}[-/]\d{4}|\d{4}[-/]\d{2}|[A-Za-z]+\s+\d{4}|present|current)\b'

        emails = re.findall(email_pattern, text)
        
        # Phone extraction 
        raw_phones = re.findall(phone_pattern, text)
        phones = []
        for p in raw_phones:
            clean_p = p.strip()
            if 10 <= sum(c.isdigit() for c in clean_p) <= 15:
                phones.append(clean_p)

        # Links extraction
        links = re.findall(link_pattern, text, re.IGNORECASE)

        # Location parsing logic
        detected_location = None
        loc_matches = re.findall(generic_location_pattern, text)
        blacklist = {"email", "phone", "resume", "curriculum", "vitae", "experience", "skills", "education", "summary"}
        for match in loc_matches:
            part1, part2 = match[0].strip(), match[1].strip()
            if part1.lower() in blacklist or part2.lower() in blacklist:
                continue
            detected_location = f"{part1}, {part2}"
            break

        # Historical Timelines (Dates)
        experience = []
        date_matches = re.findall(date_range_pattern, text, re.IGNORECASE)
        for s_date, e_date in date_matches:
            experience.append({
                "title": "Professional Experience Item",
                "company": "Extracted Corporate Entity",
                "start_date": s_date.strip(),
                "end_date": e_date.strip()
            })

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        assumed_name = lines[0].split('|')[0].strip() if lines else None

        # Skill Extraction Loop
        found_skills = []
        text_lower = text.lower()
        for skill in self.KNOWN_SKILLS:
            if re.search(rf'\b{re.escape(skill)}\b', text_lower):
                found_skills.append({
                    "name": skill,
                    "confidence": 0.7,
                    "sources": [self.source_name]
                })

        record = {
            "_source": self.source_name,
            "full_name": assumed_name,
            "email": emails[0] if emails else None,
            "phone": phones[0] if phones else None,
            "location": detected_location,
            "links": links if links else None,
            "skills": found_skills if found_skills else None,
            "experience": experience if experience else None
        }

        record = {k: v for k, v in record.items() if v is not None}
        return [record] if record else []
import re
import phonenumbers 
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urlunparse

class Normalizer:
    
    SKILL_SYNONYMS: Dict[str, str] = {
        "reactjs": "React", "react.js": "React", "reactjs": "React", "react": "React",
        "nodejs": "Node.js", "node": "Node.js", "js": "JavaScript", "javascript": "JavaScript",
        "python3": "Python", "py": "Python", "golang": "Go", "csharp": "C#", "cpp": "C++",
        "bash": "Shell", "tailwindcss": "Tailwind", "vuejs": "Vue", "vue.js": "Vue",
        "nextjs": "Next.js", "nuxtjs": "Nuxt.js", "sveltejs": "Svelte", "styles": "CSS",
        "styling": "CSS", "expressjs": "Express", "express.js": "Express", "springboot": "Spring Boot",
        "ror": "Ruby on Rails", "rails": "Ruby on Rails", "aspnet": "ASP.NET", "postgres": "PostgreSQL",
        "mssql": "Microsoft SQL Server", "sqlserver": "Microsoft SQL Server", "mongo": "MongoDB",
        "elastic": "Elasticsearch", "db": "SQL", "sklearn": "scikit-learn", "tf": "TensorFlow",
        "huggingface": "Hugging Face", "hf": "Hugging Face", "largelanguagemodels": "LLM",
        "generativeai": "LLM", "genai": "LLM", "powerbi": "Power BI", "msexcel": "Excel",
        "apachespark": "Spark", "bq": "BigQuery", "amazonwebservices": "AWS", "googlecloud": "GCP",
        "googlecloudplatform": "GCP", "k8s": "Kubernetes", "githubactions": "GitHub Actions",
        "gitlabci": "GitLab CI", "cicd": "CI/CD", "teamwork": "Teamwork", "collaboration": "Teamwork",
        "writing": "Written Communication", "documentation": "Technical Writing", "speaking": "Public Speaking",
        "leadership": "Team Leadership", "crossfunctionalcollaboration": "Cross-Functional Collaboration",
        "interpersonalskills": "Interpersonal Skills", "problemsolving": "Problem Solving",
        "criticalthinking": "Critical Thinking", "timemanagement": "Time Management", "activelistening": "Active Listening"
    }

    @staticmethod
    def normalize_email(email: Optional[str]) -> Optional[str]:
        if not email:
            return None
        return str(email).strip().lower()

    @staticmethod
    def normalize_phone(phone: Optional[str], region: str = "IN") -> Optional[str]:
        if not phone:
            return None
        try:
            clean_phone = str(phone).strip()
            if not clean_phone.startswith('+') and not clean_phone.startswith('00'):
                parsed = phonenumbers.parse(clean_phone, region)
            else:
                parsed = phonenumbers.parse(clean_phone, None)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            pass
        return None

    @staticmethod
    def normalize_skill(skill: Optional[str]) -> Optional[str]:
        if not skill:
            return None
        clean_skill = re.sub(r'[^a-z0-9#\+\.]', '', str(skill).lower().strip())
        return Normalizer.SKILL_SYNONYMS.get(clean_skill, str(skill).strip())

    @staticmethod
    def normalize_link(url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        try:
            url_str = str(url).strip().lower()
            if not url_str.startswith(('http://', 'https://')):
                url_str = 'https://' + url_str
            parsed = urlparse(url_str)
            cleaned_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
            return cleaned_url
        except Exception:
            return url

    @staticmethod
    def normalize_date(date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None
        ds = str(date_str).strip()
        if ds.lower() in ["present", "current", "now"]:
            return "Present"
        
        # Strip internal noise characters
        date_clean = re.sub(r'[\s\/.]', '-', ds)
        
        # Pattern 1: ISO matching (YYYY-MM-DD or YYYY-MM)
        match_iso = re.match(r'^(\d{4})-(\d{2})', date_clean)
        if match_iso:
            return f"{match_iso.group(1)}-{match_iso.group(2)}"
            
        # Pattern 2: Structural components inversion parsing (DD-MM-YYYY)
        tokens = re.findall(r'(\d{2,4})', date_clean)
        if len(tokens) >= 2:
            if len(tokens[-1]) == 4:  # Year at end
                return f"{tokens[-1]}-{tokens[-2]}"
            elif len(tokens[0]) == 4: # Year at front
                return f"{tokens[0]}-{tokens[1]}"
        return None

    @staticmethod
    def normalize_location(loc_raw: Any) -> Dict[str, Optional[str]]:
        result = {"city": None, "region": None, "country": "IN"}
        if not loc_raw:
            return result
            
        if isinstance(loc_raw, dict):
            result["city"] = loc_raw.get("city") or loc_raw.get("town")
            result["region"] = loc_raw.get("region") or loc_raw.get("state")
            country = loc_raw.get("country")
            if country and len(str(country)) == 2:
                result["country"] = str(country).upper()
            return result

        parts = [p.strip() for p in str(loc_raw).split(",")]
        if len(parts) == 1:
            result["city"] = parts[0]
        elif len(parts) == 2:
            result["city"] = parts[0]
            last_part_lower = parts[1].lower()
            if last_part_lower in ["india", "ind", "united states", "usa", "us", "uk"]:
                result["region"] = None
                parts.append(parts[1]) 
            else:
                result["region"] = parts[1]
        elif len(parts) >= 3:
            result["city"] = parts[0]
            result["region"] = parts[1]
                
        last_word = str(parts[-1]).lower()
        if last_word in ["india", "ind", "in"]:
            result["country"] = "IN"
        elif last_word in ["united states", "usa", "us"]:
            result["country"] = "US"
        elif last_word in ["united kingdom", "uk", "gb"]:
            result["country"] = "GB"
            
        return result
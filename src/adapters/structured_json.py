import json
from typing import List, Dict, Any
from src.adapters.base_adapter import BaseAdapter  

class StructuredJsonAdapter(BaseAdapter):
    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        records = []
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                raw_data = json.load(f)

            raw_items = []
            if isinstance(raw_data, list):
                raw_items = raw_data
            elif isinstance(raw_data, dict):
                possible_list_keys = ["candidates", "recruiters", "results", "data", "items"]
                for key in possible_list_keys:
                    if key in raw_data and isinstance(raw_data[key], list):
                        raw_items = raw_data[key]
                        break
                else:
                    raw_items = [raw_data]

            for item in raw_items:
                if not isinstance(item, dict):
                    continue

                clean_row = {
                    str(k).strip().lower().replace(" ", "_").replace("-", "_"): v
                    for k, v in item.items() if k and v is not None
                }

                contact_info = clean_row.get("contact") or clean_row.get("contact_info") or {}
                profile_info = clean_row.get("profile") or {}
                if not isinstance(contact_info, dict): contact_info = {}
                if not isinstance(profile_info, dict): profile_info = {}

                # Identity Mapping
                name = clean_row.get("name") or clean_row.get("full_name") or clean_row.get("candidate_name") or profile_info.get("name") or contact_info.get("name")
                email = clean_row.get("email") or clean_row.get("email_address") or contact_info.get("email")
                phone = clean_row.get("phone") or clean_row.get("phone_number") or clean_row.get("mobile") or contact_info.get("phone")
                company = clean_row.get("company") or clean_row.get("current_company") or profile_info.get("company")
                title = clean_row.get("title") or clean_row.get("job_title") or clean_row.get("role") or profile_info.get("title")

                # Extract Locations
                location = clean_row.get("location") or profile_info.get("location") or clean_row.get("city")

                # Extract Portfolio Hyperlinks
                links = clean_row.get("links") or clean_row.get("urls") or profile_info.get("links") or []
                if isinstance(links, str):
                    links = [lnk.strip() for lnk in links.split(",") if lnk.strip()]

                # Extract Skills
                skills = []
                skills_raw = clean_row.get("skills") or profile_info.get("skills") or []
                if isinstance(skills_raw, str):
                    skills_raw = [s.strip() for s in skills_raw.split(",") if s.strip()]
                
                if isinstance(skills_raw, list):
                    for sk in skills_raw:
                        if isinstance(sk, dict) and sk.get("name"):
                            skills.append({"name": str(sk["name"]), "confidence": float(sk.get("confidence", 0.9)), "sources": [self.source_name]})
                        elif isinstance(sk, str):
                            skills.append({"name": sk, "confidence": 0.9, "sources": [self.source_name]})

                # Extract Experience timelines
                experience = []
                exp_raw = clean_row.get("experience") or clean_row.get("history") or []
                if isinstance(exp_raw, list):
                    for e in exp_raw:
                        if isinstance(e, dict):
                            experience.append({
                                "title": e.get("title") or e.get("role"),
                                "company": e.get("company") or e.get("employer"),
                                "start_date": e.get("start_date") or e.get("from"),
                                "end_date": e.get("end_date") or e.get("to") or "Present"
                            })

                record = {
                    "_source": self.source_name,
                    "full_name": name,
                    "email": email,
                    "phone": phone,
                    "current_company": company,
                    "title": title,
                    "location": location,
                    "links": links if links else None,
                    "skills": skills if skills else None,
                    "experience": experience if experience else None
                }

                record = {k: v for k, v in record.items() if v is not None}
                if len(record) > 1:
                    records.append(record)
        except Exception as e:
            print(f"Error parsing JSON {file_path}: {e}")

        return records
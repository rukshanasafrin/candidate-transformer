import csv
from typing import List, Dict, Any
from src.adapters.base_adapter import BaseAdapter


class CsvAdapter(BaseAdapter):
    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        records = []
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    clean_row = {
                        k.strip().lower().replace(" ", "_"): v.strip()
                        for k, v in row.items() if k and v
                    }

                    # Base Identity Info
                    name = clean_row.get("name") or clean_row.get("full_name") or clean_row.get("candidate")
                    email = clean_row.get("email") or clean_row.get("email_address")
                    phone = clean_row.get("phone") or clean_row.get("phone_number") or clean_row.get("mobile")
                    company = clean_row.get("company") or clean_row.get("current_company")
                    title = clean_row.get("title") or clean_row.get("job_title")

                    # Location string processing
                    location = clean_row.get("location") or clean_row.get("city") or clean_row.get("address")

                    # Handle Portfolio Links
                    links = []
                    link_raw = clean_row.get("links") or clean_row.get("urls") or clean_row.get("portfolio")
                    if link_raw:
                        links = [lnk.strip() for lnk in link_raw.split(",") if lnk.strip()]

                    # Handle Skills array parsing
                    skills = []
                    skills_raw = clean_row.get("skills") or clean_row.get("skills_list")
                    if skills_raw:
                        skills = [{"name": sk.strip(), "confidence": 0.8, "sources": [self.source_name]} 
                                  for sk in skills_raw.split(",") if sk.strip()]

                    # Handle Timeline (Dates)
                    experience = []
                    start_date = clean_row.get("start_date") or clean_row.get("join_date")
                    end_date = clean_row.get("end_date") or clean_row.get("exit_date")
                    if start_date or end_date or company or title:
                        experience.append({
                            "title": title,
                            "company": company,
                            "start_date": start_date,
                            "end_date": end_date or "Present"
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
            print(f"Error parsing CSV {file_path}: {e}")

        return records


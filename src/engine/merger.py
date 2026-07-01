from typing import List, Dict, Any, Optional
from src.engine.normalizer import Normalizer
from src.engine.schemas import CanonicalCandidateProfile, LocationSchema
import re

class Merger:
    # Updated: Added evaluation confidence scores for new adapters
    SOURCE_CONFIDENCE = {
        "ats_json": 0.9,
        "recruiter_csv": 0.8,
        "resume_pdf": 0.6,
        "resume_text": 0.6,
        "resume_markdown": 0.6,
        "recruiter_notes": 0.5
    }

    def __init__(self):
        self.candidates_db: Dict[str, Dict[str, Any]] = {}

    def _find_profile_id(self, email: Optional[str], phone: Optional[str], name: Optional[str], company: Optional[str]) -> Optional[str]:
        # Priority 1: Email Match
        if email and email in self.candidates_db:
            return email
            
        # Priority 2: Phone Match
        if phone:
            for pid, profile in self.candidates_db.items():
                if phone in profile.get("phones", []):
                    return pid
                    
        # Priority 3: Normalized Name + Current Company Match
        if name and company:
            norm_name = re.sub(r'[^a-z]', '', name.lower().strip())
            norm_comp = re.sub(r'[^a-z]', '', company.lower().strip())
            for pid, profile in self.candidates_db.items():
                p_name = profile.get("full_name")
                p_comp = profile.get("current_company")
                if p_name and p_comp:
                    p_norm_name = re.sub(r'[^a-z]', '', p_name.lower().strip())
                    p_norm_comp = re.sub(r'[^a-z]', '', p_comp.lower().strip())
                    if norm_name == p_norm_name and norm_comp == p_norm_comp:
                        return pid
        return None

    def process_records(self, records: List[Dict[str, Any]]):
        for record in records:
            source = record.get("_source", "unknown")
            confidence = self.SOURCE_CONFIDENCE.get(source, 0.5)

            norm_email = Normalizer.normalize_email(record.get("email"))
            norm_phone = Normalizer.normalize_phone(record.get("phone"))
            raw_name = record.get("full_name")
            raw_company = record.get("current_company")

            # Ignore records missing all core identifiers
            if not norm_email and not norm_phone and not raw_name:
                continue

            pid = self._find_profile_id(norm_email, norm_phone, raw_name, raw_company)

            if not pid:
                pid = norm_email if norm_email else (f"phone_{norm_phone}" if norm_phone else f"anon_{hash(raw_name)}")
                self.candidates_db[pid] = {
                    "candidate_id": pid,
                    "emails": [norm_email] if norm_email else [],
                    "phones": [norm_phone] if norm_phone else [],
                    "location": LocationSchema(city=None, region=None, country="IN"),
                    "links": [],
                    "skills": [],
                    "experience": [],
                    "provenance": [],
                    "full_name": None,
                    "current_company": None,
                    "title": None,
                    "_highest_conf_dict": {}
                }

            self._merge_record(self.candidates_db[pid], record, norm_email, norm_phone)

    def _merge_record(self, profile: Dict[str, Any], record: Dict[str, Any], norm_email: Optional[str], norm_phone: Optional[str]):
        source = record.get("_source", "unknown")
        confidence = self.SOURCE_CONFIDENCE.get(source, 0.5)
        h_conf = profile["_highest_conf_dict"]

        # Winner Determinations for Scalar Fields
        for scalar_field in ["full_name", "current_company", "title"]:
            val = record.get(scalar_field)
            if val:
                if confidence > h_conf.get(scalar_field, 0.0):
                    profile[scalar_field] = val
                    h_conf[scalar_field] = confidence
                    self._add_provenance(profile, scalar_field, source, "exact_match")

        # Unique Flattened List Append Strategy for Core Vectors
        if norm_email and norm_email not in profile["emails"]:
            profile["emails"].append(norm_email)
        if norm_phone and norm_phone not in profile["phones"]:
            profile["phones"].append(norm_phone)

        # Merge & Normalize Location Data Block
        if record.get("location"):
            if confidence > h_conf.get("location", 0.0):
                norm_loc = Normalizer.normalize_location(record["location"])
                profile["location"].city = norm_loc["city"]
                profile["location"].region = norm_loc["region"]
                profile["location"].country = norm_loc["country"]
                h_conf["location"] = confidence
                self._add_provenance(profile, "location", source, "geoparsing_standard")

        # Unique Links Flattening
        if record.get("links"):
            for link in record["links"]:
                norm_link = Normalizer.normalize_link(link)
                if norm_link and norm_link not in profile["links"]:
                    profile["links"].append(norm_link)
                    self._add_provenance(profile, f"links[{len(profile['links'])-1}]", source, "param_stripping")

        # Unique Job Experience Matrix Tracking
        if record.get("experience"):
            for exp in record["experience"]:
                clean_exp = {
                    "title": exp.get("title"),
                    "company": exp.get("company"),
                    "start_date": Normalizer.normalize_date(exp.get("start_date")),
                    "end_date": Normalizer.normalize_date(exp.get("end_date"))
                }
                if clean_exp not in profile["experience"]:
                    profile["experience"].append(clean_exp)

        # Canonical Skills Deduplication Deductor
        if "skills" in record:
            for new_skill in record["skills"]:
                raw_n = new_skill.get("name") if isinstance(new_skill, dict) else str(new_skill)
                canonical_name = Normalizer.normalize_skill(raw_n)
                if not canonical_name:
                    continue

                existing_skill = next((s for s in profile["skills"] if s["name"] == canonical_name), None)
                if existing_skill:
                    if source not in existing_skill["sources"]:
                        existing_skill["sources"].append(source)
                else:
                    profile["skills"].append({
                        "name": canonical_name,
                        "confidence": float(new_skill.get("confidence", 0.7)) if isinstance(new_skill, dict) else 0.7,
                        "sources": [source]
                    })

    def _add_provenance(self, profile: Dict[str, Any], field: str, source: str, method: str):
        profile["provenance"].append({
            "field": field,
            "source": source,
            "method": method
        })

    def get_canonical_profiles(self) -> List[CanonicalCandidateProfile]:
        profiles = []
        for pid, data in list(self.candidates_db.items()):
            # Cleanup engine variables before serialization
            data.pop("_highest_conf_dict", None)
            data.pop("current_company", None)
            data.pop("title", None)
            data["overall_confidence"] = 0.85
            try:
                valid_profile = CanonicalCandidateProfile(**data)
                profiles.append(valid_profile)
            except Exception as e:
                print(f"Validation dropout for {pid}: {e}")
        return profiles
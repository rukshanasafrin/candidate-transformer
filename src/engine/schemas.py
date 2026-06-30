from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LocationSchema(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = "IN"

class SkillSchema(BaseModel):
    name: str
    confidence: float = 0.7
    sources: List[str]

class HistoryItemSchema(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = Field(None, description="YYYY-MM format")
    end_date: Optional[str] = Field(None, description="YYYY-MM format")

class ProvenanceSchema(BaseModel):
    field: str
    source: str
    method: str

class CanonicalCandidateProfile(BaseModel):
    candidate_id: str
    full_name: Optional[str] = None
    emails: List[str] = []
    phones: List[str] = []
    location: LocationSchema = Field(default_factory=LocationSchema)
    links: List[str] = []
    skills: List[SkillSchema] = []
    experience: List[HistoryItemSchema] = []
    provenance: List[ProvenanceSchema] = []
    overall_confidence: float = 0.85
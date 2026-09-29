"""Typed Pydantic models — the contract between frontend, dialogue engine and recommender."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Profile
# --------------------------------------------------------------------------- #

# Canonical, ordered list of profile slots. "name" is optional and never blocks
# completion; everything else must be filled before recommendations unlock.
PROFILE_FIELDS: list[str] = [
    "name",
    "age",
    "district",
    "education",
    "family_occupation",
    "current_livelihood",
    "skills",
    "interests",
    "constraints",
    "preference",
    "mobility",
]

REQUIRED_FIELDS: list[str] = [f for f in PROFILE_FIELDS if f != "name"]


class EducationLevel(str, Enum):
    none = "none"          # no formal schooling
    grade5 = "grade5"
    grade8 = "grade8"
    grade10 = "grade10"
    grade12 = "grade12"
    iti = "iti"
    diploma = "diploma"
    graduate = "graduate"


EDUCATION_ORDER: dict[str, int] = {
    "none": 0, "grade5": 1, "grade8": 2, "grade10": 3,
    "grade12": 4, "iti": 5, "diploma": 6, "graduate": 7,
}

# Plain labels used in voice read-back (Hindi + English).
EDUCATION_LABELS: dict[str, str] = {
    "none": "कोई औपचारिक पढ़ाई नहीं / no formal schooling",
    "grade5": "5वीं तक / 5th grade",
    "grade8": "8वीं तक / 8th grade",
    "grade10": "10वीं तक / 10th grade",
    "grade12": "12वीं तक / 12th grade",
    "iti": "आईटीआई / ITI",
    "diploma": "डिप्लोमा / Diploma",
    "graduate": "स्नातक / Graduate",
}


class Preference(str, Enum):
    self_employment = "self_employment"
    wage_job = "wage_job"
    either = "either"
    unknown = "unknown"


class Profile(BaseModel):
    """Beneficiary profile. Lists hold canonical lowercase tags (e.g. 'sewing')."""

    name: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=14, le=100)
    district: Optional[str] = None
    state: Optional[str] = None
    education: Optional[EducationLevel] = None
    family_occupation: Optional[str] = None
    current_livelihood: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    constraints: Optional[str] = None  # physical / mobility / other constraints
    preference: Optional[Preference] = None
    mobility: Optional[str] = None  # "willing" | "limited" | "unknown"
    skipped_fields: list[str] = Field(default_factory=list)

    def missing_fields(self) -> list[str]:
        missing = []
        for f in REQUIRED_FIELDS:
            val = getattr(self, f)
            if val is None or val == "" or val == [] or val == Preference.unknown or val == "unknown":
                missing.append(f)
        return missing

    def is_complete(self) -> bool:
        return len(self.missing_fields()) == 0

    def as_field_dict(self) -> dict:
        return self.model_dump(mode="json")


# --------------------------------------------------------------------------- #
# Conversation
# --------------------------------------------------------------------------- #

class ConsentRequest(BaseModel):
    locale: str = "hi-IN"
    consent_given: bool = True


class SessionOut(BaseModel):
    session_id: str
    consent_text: str
    consent_text_en: str
    consent_read_text: str  # what TTS should speak


class TurnRequest(BaseModel):
    session_id: str
    user_text: str = Field(min_length=1, max_length=2000)


class TurnResponse(BaseModel):
    reply_text: str
    reply_text_en: str
    extracted_fields: dict = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    is_complete: bool = False
    current_question_field: Optional[str] = None
    tap_options: list[str] = Field(default_factory=list)
    engine: str = "rules"  # "llm" | "rules" | "llm+rules"
    warning: Optional[str] = None  # e.g. "LLM unavailable — using friendly offline mode"


class ConfirmRequest(BaseModel):
    session_id: str
    user_text: Optional[str] = None  # corrections like "umar 26 hai"


class ConfirmResponse(BaseModel):
    readback_text: str
    readback_text_en: str
    profile: Profile
    is_confirmed: bool
    reply_text: str


class DeleteResponse(BaseModel):
    deleted: bool
    detail: str


# --------------------------------------------------------------------------- #
# Recommendations
# --------------------------------------------------------------------------- #

class ScoreBreakdown(BaseModel):
    similarity: float = Field(ge=0, le=1)         # profile ↔ role text match (TF-IDF)
    education: float = Field(ge=0, le=1)          # eligibility
    demand: float = Field(ge=0, le=1)             # local district demand
    mobility: float = Field(ge=0, le=1)           # physical / travel fit
    preference: float = Field(ge=0, le=1)         # self-employment vs wage fit
    total: float = Field(ge=0, le=1)
    notes: dict[str, str] = Field(default_factory=dict)  # plain-language reason per component


class SkillGap(BaseModel):
    skill_name: str
    covered: bool
    note: str  # "already familiar" | "will be taught in training"


class TrainingCenter(BaseModel):
    name: str
    distance_km: Optional[float] = None
    sector_tags: list[str] = Field(default_factory=list)
    note: str = ""


class Recommendation(BaseModel):
    rank: int
    role_id: str
    job_role: str
    sector: str
    nsqf_level: int
    min_education: str
    duration_hours: int
    duration_display: str
    why_it_fits: str
    skill_gaps: list[SkillGap]
    skill_match_percent: int = Field(ge=0, le=100)
    nearest_center: Optional[TrainingCenter] = None
    scheme_pointer: str
    physical_demand: str
    self_employment_potential: str
    score: int = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    eligibility_note: str = ""


class RecommendRequest(BaseModel):
    profile: Profile


class RecommendResponse(BaseModel):
    recommendations: list[Recommendation]
    generated_offline: bool = True  # engine never needs internet — seed data is local
    data_notice: str
    district_note: str = ""


class MetaOut(BaseModel):
    app_name: str
    version: str
    data_notice: str
    honesty_note: str
    languages: list[str]

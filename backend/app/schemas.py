from datetime import date, datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileIn(BaseModel):
    user_type: str = "student"
    name: str = ""
    college: str = ""
    degree: str = ""
    graduation_year: Optional[int] = None
    branch: str = ""
    years_experience: int = 0
    current_role: str = ""
    target_roles: List[str] = []
    preferred_locations: List[str] = ["India"]
    preferred_types: List[str] = ["Internship"]
    preferred_tiers: List[str] = ["S", "A"]
    women_focused: bool = False
    skills: List[str] = []


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)


class OpportunityOut(BaseModel):
    id: int
    title: str
    organization: str
    opportunity_type: str
    role: str
    description: str
    source_url: str
    source_name: str
    deadline: Optional[date]
    location: str
    experience_min: int
    experience_max: int
    company_tier: str
    eligible_branches: List[Literal["CSE", "ECE", "AIML"]] = []
    inferred_company_tier: str = "Unrated"
    verified: bool
    women_focused: bool
    skills: List[str] = []
    match_score: Optional[int] = None
    semantic_score: Optional[int] = None
    reasons: List[str] = []


class InteractionIn(BaseModel):
    event_type: Literal["view", "save", "apply", "dismiss"]


class ApplicationIn(BaseModel):
    status: Literal["saved", "applied", "interview", "offer", "rejected", "withdrawn"] = "saved"
    notes: str = ""
    applied_at: Optional[datetime] = None
    follow_up_date: Optional[date] = None


class NotificationPreferenceIn(BaseModel):
    email_enabled: bool = True
    deadline_alerts: bool = True
    daily_digest: bool = True
    telegram_enabled: bool = False
    telegram_chat_id: str = ""
    digest_hour: int = 9


class RecommendationPreferenceIn(BaseModel):
    target_companies: List[str] = []
    target_seniority: Literal["auto", "intern", "junior", "mid", "senior", "lead"] = "auto"


class UserReportIn(BaseModel):
    reason: Literal["incorrect", "expired", "spam", "unsafe", "duplicate", "other"]
    details: str = ""


class ModerationIn(BaseModel):
    status: Literal["pending", "approved", "rejected", "needs_review"]
    reason: str = ""


class OpportunityCreate(BaseModel):
    title: str
    organization: str
    opportunity_type: str
    role: str = ""
    description: str = ""
    source_url: str
    source_name: str
    deadline: Optional[date] = None
    location: str = "India"
    experience_min: int = 0
    experience_max: int = 0
    company_tier: str = "Unrated"
    eligible_branches: List[Literal["CSE", "ECE", "AIML"]] = []
    verified: bool = False
    women_focused: bool = False
    skills: List[str] = []

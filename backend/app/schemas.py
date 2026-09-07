from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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
    inferred_company_tier: str = "Unrated"
    verified: bool
    women_focused: bool
    skills: List[str] = []
    match_score: Optional[int] = None
    semantic_score: Optional[int] = None
    reasons: List[str] = []


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
    verified: bool = False
    women_focused: bool = False
    skills: List[str] = []

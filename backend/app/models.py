from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship
from .database import Base

user_skills = Table(
    "user_skills",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id"), primary_key=True),
)

opportunity_skills = Table(
    "opportunity_skills",
    Base.metadata,
    Column("opportunity_id", ForeignKey("opportunities.id"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    skills = relationship("Skill", secondary=user_skills, back_populates="users")
    saved = relationship("SavedOpportunity", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    user_type = Column(String(30), default="student")  # student | professional
    name = Column(String(120), default="")
    college = Column(String(200), default="")
    degree = Column(String(120), default="")
    graduation_year = Column(Integer, nullable=True)
    branch = Column(String(120), default="")
    years_experience = Column(Integer, default=0)
    current_role = Column(String(120), default="")
    target_roles = Column(String(500), default="")  # comma-separated
    preferred_locations = Column(String(500), default="")  # comma-separated
    preferred_types = Column(String(500), default="")  # comma-separated
    preferred_tiers = Column(String(200), default="S,A")
    women_focused = Column(Boolean, default=False)

    user = relationship("User", back_populates="profile")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, index=True, nullable=False)

    users = relationship("User", secondary=user_skills, back_populates="skills")
    opportunities = relationship("Opportunity", secondary=opportunity_skills, back_populates="skills")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
    organization = Column(String(200), nullable=False)
    opportunity_type = Column(String(80), nullable=False)
    role = Column(String(120), default="")
    description = Column(Text, default="")
    source_url = Column(String(1000), nullable=False)
    source_name = Column(String(200), nullable=False)
    deadline = Column(Date, nullable=True)
    location = Column(String(200), default="India")
    experience_min = Column(Integer, default=0)
    experience_max = Column(Integer, default=0)
    company_tier = Column(String(10), default="Unrated")
    verified = Column(Boolean, default=False)
    women_focused = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    skills = relationship("Skill", secondary=opportunity_skills, back_populates="opportunities")


class SavedOpportunity(Base):
    __tablename__ = "saved_opportunities"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved")

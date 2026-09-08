from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Table, Text
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
    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("NotificationDelivery", back_populates="user", cascade="all, delete-orphan")
    recommendation_preferences = relationship("RecommendationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reports = relationship("UserReport", back_populates="user", cascade="all, delete-orphan")


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
    eligible_branches = Column(String(30), default="")
    verified = Column(Boolean, default=False)
    women_focused = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    skills = relationship("Skill", secondary=opportunity_skills, back_populates="opportunities")
    interactions = relationship("Interaction", back_populates="opportunity", cascade="all, delete-orphan")
    source_health = relationship("SourceHealth", back_populates="opportunity", uselist=False, cascade="all, delete-orphan")
    moderation = relationship("OpportunityModeration", back_populates="opportunity", uselist=False, cascade="all, delete-orphan")
    reports = relationship("UserReport", back_populates="opportunity", cascade="all, delete-orphan")


class SavedOpportunity(Base):
    __tablename__ = "saved_opportunities"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved")
    opportunity = relationship("Opportunity")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (Index("ix_applications_user_status", "user_id", "status"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    status = Column(String(30), default="saved", nullable=False)
    notes = Column(Text, default="")
    applied_at = Column(DateTime, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="applications")
    opportunity = relationship("Opportunity")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True)
    deadline_alerts = Column(Boolean, default=True)
    daily_digest = Column(Boolean, default=True)
    telegram_enabled = Column(Boolean, default=False)
    telegram_chat_id = Column(String(100), default="")
    digest_hour = Column(Integer, default=9)

    user = relationship("User", back_populates="notification_preferences")


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (Index("ix_notification_deliveries_user_created", "user_id", "created_at"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel = Column(String(30), nullable=False)
    notification_type = Column(String(40), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(30), default="queued", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class Interaction(Base):
    __tablename__ = "interactions"
    __table_args__ = (Index("ix_interactions_user_opportunity", "user_id", "opportunity_id"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    event_type = Column(String(30), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    opportunity = relationship("Opportunity", back_populates="interactions")


class RecommendationPreference(Base):
    __tablename__ = "recommendation_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    target_companies = Column(String(1000), default="")
    target_seniority = Column(String(40), default="auto")

    user = relationship("User", back_populates="recommendation_preferences")


class SourceHealth(Base):
    __tablename__ = "source_health"

    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), unique=True, nullable=False)
    check_status = Column(String(30), default="unknown", nullable=False)
    http_status = Column(Integer, nullable=True)
    checked_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0)
    last_error = Column(String(500), default="")

    opportunity = relationship("Opportunity", back_populates="source_health")


class OpportunityModeration(Base):
    __tablename__ = "opportunity_moderation"

    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), unique=True, nullable=False)
    status = Column(String(30), default="pending", nullable=False)
    reason = Column(String(500), default="")
    reviewed_at = Column(DateTime, nullable=True)

    opportunity = relationship("Opportunity", back_populates="moderation")


class UserReport(Base):
    __tablename__ = "user_reports"
    __table_args__ = (Index("ix_user_reports_status", "status"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    reason = Column(String(80), nullable=False)
    details = Column(Text, default="")
    status = Column(String(30), default="open", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reports")
    opportunity = relationship("Opportunity", back_populates="reports")

from datetime import date, timedelta
from .database import Base, SessionLocal, engine
from .models import Opportunity, Skill, User, Profile
from .auth import hash_password

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

demo = User(email="demo@student.com", password_hash=hash_password("password123"))
db.add(demo)
db.flush()

profile = Profile(
    user_id=demo.id,
    user_type="student",
    name="Demo Student",
    college="IIIT Bangalore",
    degree="Integrated M.Tech",
    graduation_year=2028,
    branch="Computer Science",
    years_experience=0,
    target_roles="SDE,MLE,Research",
    preferred_locations="India,Bangalore,Remote",
    preferred_types="Internship,Research,Hackathon,Scholarship,Open Source",
    preferred_tiers="S,A",
    women_focused=True,
)
db.add(profile)

def get_skill(name):
    skill = db.query(Skill).filter(Skill.name == name).first()
    if not skill:
        skill = Skill(name=name)
        db.add(skill)
        db.flush()
    return skill

def add_opportunity(
    title, org, typ, role, skills, tier, deadline, location,
    source_name, source_url, verified=True, women=False
):
    op = Opportunity(
        title=title,
        organization=org,
        opportunity_type=typ,
        role=role,
        description=f"{title} by {org}. Build experience in {role}.",
        source_url=source_url,
        source_name=source_name,
        deadline=deadline,
        location=location,
        company_tier=tier,
        verified=verified,
        women_focused=women,
    )
    op.skills = [get_skill(s) for s in skills]
    db.add(op)

today = date.today()
add_opportunity(
    "Software Engineering Internship", "Google", "Internship", "SDE",
    ["Python", "C++", "DSA"], "S", today + timedelta(days=12),
    "Bangalore/Remote", "Google Careers", "https://www.google.com/about/careers/applications/"
)
add_opportunity(
    "AI/ML Research Internship", "IISc", "Research", "Research",
    ["Python", "PyTorch", "Machine Learning"], "S", today + timedelta(days=18),
    "Bangalore", "IISc", "https://iisc.ac.in/"
)
add_opportunity(
    "AI Innovation Hackathon", "Microsoft", "Hackathon", "SDE",
    ["Python", "React", "Machine Learning"], "A", today + timedelta(days=5),
    "Remote", "Microsoft", "https://www.microsoft.com/en-in/"
)
add_opportunity(
    "Women in Tech Scholarship", "Example Foundation", "Scholarship", "Research",
    ["Python"], "A", today + timedelta(days=25),
    "India", "Official Program", "https://example.com/women-scholarship", women=True
)
add_opportunity(
    "Open Source Mentorship", "Open Source Community", "Open Source", "SDE",
    ["C++", "Python", "Git"], "B", today + timedelta(days=30),
    "Remote", "Official Program", "https://opensource.guide/"
)
add_opportunity(
    "Random Marketing Internship", "Small Agency", "Internship", "Marketing",
    ["Excel"], "C", today + timedelta(days=3),
    "Delhi", "Unknown Board", "https://example.com/random", verified=False
)

# Demo user skills
demo.skills = [get_skill(s) for s in ["Python", "C++", "Machine Learning", "PyTorch", "Git"]]

db.commit()
db.close()

print("Seed complete.")
print("Demo login: demo@student.com / password123")

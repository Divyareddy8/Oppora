from datetime import date, timedelta
from .database import Base, SessionLocal, engine
from .matching import infer_eligible_branches, normalize_branches
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
    source_name, source_url, verified=True, women=False, experience_min=0, experience_max=2, eligible_branches=None
):
    description = f"{title} by {org}. Build experience in {role}."
    op = Opportunity(
        title=title,
        organization=org,
        opportunity_type=typ,
        role=role,
        description=description,
        source_url=source_url,
        source_name=source_name,
        deadline=deadline,
        location=location,
        company_tier=tier,
        verified=verified,
        women_focused=women,
        experience_min=experience_min,
        experience_max=experience_max,
        eligible_branches=",".join(normalize_branches(eligible_branches or infer_eligible_branches(title, description))),
    )
    op.skills = [get_skill(s) for s in skills]
    db.add(op)

today = date.today()
add_opportunity(
    "Software Engineering Internship", "Google", "Internship", "SDE",
    ["Python", "C++", "DSA"], "S", today + timedelta(days=12),
    "Bangalore/Remote", "Google Careers", "https://www.google.com/about/careers/applications/", eligible_branches=["CSE", "AIML"]
)
add_opportunity(
    "Backend Engineer", "Swiggy", "Job", "Software Engineer",
    ["Python", "Go", "PostgreSQL"], "A", today + timedelta(days=40),
    "Bangalore", "Swiggy Careers", "https://careers.swiggy.com/", experience_min=2, experience_max=5
)
add_opportunity(
    "Software Development Engineer", "Flipkart", "Job", "SDE",
    ["Java", "Python", "Kubernetes"], "A", today + timedelta(days=35),
    "Bangalore", "Flipkart Careers", "https://www.flipkartcareers.com/", experience_min=1, experience_max=4
)
add_opportunity(
    "Machine Learning Engineer", "Microsoft", "Job", "MLE",
    ["Python", "Azure", "Machine Learning"], "S", today + timedelta(days=45),
    "Hyderabad", "Microsoft Careers", "https://careers.microsoft.com/", experience_min=2, experience_max=6, eligible_branches=["CSE", "AIML"]
)
add_opportunity(
    "Cloud Software Engineer", "Amazon", "Job", "Software Engineer",
    ["Java", "AWS", "Distributed Systems"], "S", today + timedelta(days=42),
    "Hyderabad", "Amazon Jobs", "https://www.amazon.jobs/en/", experience_min=3, experience_max=8
)
add_opportunity(
    "Full Stack Engineer", "Zoho", "Job", "Software Engineer",
    ["Java", "React", "SQL"], "A", today + timedelta(days=28),
    "Chennai", "Zoho Careers", "https://www.zoho.com/careers/", experience_min=1, experience_max=4
)
add_opportunity(
    "Data Engineer", "Freshworks", "Job", "Data Engineer",
    ["Python", "SQL", "Data Engineering"], "A", today + timedelta(days=32),
    "Chennai", "Freshworks Careers", "https://www.freshworks.com/company/careers/", experience_min=2, experience_max=5
)
add_opportunity(
    "Product Engineer", "Dream11", "Job", "Software Engineer",
    ["Java", "React", "AWS"], "A", today + timedelta(days=38),
    "Mumbai", "Dream Sports Careers", "https://www.dreamsports.group/careers/", experience_min=2, experience_max=6
)
add_opportunity(
    "Analytics Engineer", "Tata Digital", "Job", "Data Scientist",
    ["Python", "SQL", "Analytics"], "A", today + timedelta(days=30),
    "Mumbai", "Tata Careers", "https://www.tata.com/careers", experience_min=1, experience_max=5
)
add_opportunity(
    "Platform Engineer", "MakeMyTrip", "Job", "Software Engineer",
    ["Java", "Kubernetes", "AWS"], "A", today + timedelta(days=36),
    "Gurgaon", "MakeMyTrip Careers", "https:// careers.makemytrip.com/".replace(" ", ""), experience_min=3, experience_max=7
)
add_opportunity(
    "Applied Scientist", "Adobe", "Job", "Research",
    ["Python", "PyTorch", "Machine Learning"], "A", today + timedelta(days=50),
    "Gurgaon", "Adobe Careers", "https://www.adobe.com/careers.html", experience_min=2, experience_max=6
)
add_opportunity(
    "Software Engineer Intern", "Atlassian", "Internship", "SDE",
    ["Java", "Python", "React"], "S", today + timedelta(days=20),
    "Bangalore", "Atlassian Careers", "https://www.atlassian.com/company/careers", experience_min=0, experience_max=1
)
add_opportunity(
    "Embedded Systems Intern", "Qualcomm", "Internship", "Embedded Engineer",
    ["C", "C++", "Embedded Systems"], "S", today + timedelta(days=22),
    "Hyderabad", "Qualcomm Careers", "https://www.qualcomm.com/company/careers", experience_min=0, experience_max=1, eligible_branches=["ECE"]
)
add_opportunity(
    "AI Hardware Intern", "NVIDIA", "Internship", "AI Hardware Engineer",
    ["C++", "CUDA", "Machine Learning"], "S", today + timedelta(days=24),
    "Bangalore", "NVIDIA Careers", "https://www.nvidia.com/en-us/about-nvidia/careers/", experience_min=0, experience_max=1, eligible_branches=["ECE", "AIML"]
)
add_opportunity(
    "Embedded Firmware Engineer", "Nokia", "Job", "Embedded Engineer",
    ["C", "C++", "Embedded Systems"], "A", today + timedelta(days=29),
    "Chennai", "Nokia Careers", "https://www.nokia.com/about-us/careers/", experience_min=1, experience_max=4, eligible_branches=["ECE"]
)
add_opportunity(
    "Associate Software Engineer", "Walmart Global Tech", "Job", "SDE",
    ["Java", "Python", "Cloud"], "A", today + timedelta(days=34),
    "Chennai", "Walmart Careers", "https://careers.walmart.com/", experience_min=0, experience_max=3
)
add_opportunity(
    "AI/ML Research Internship", "IISc", "Research", "Research",
    ["Python", "PyTorch", "Machine Learning"], "S", today + timedelta(days=18),
    "Bangalore", "IISc", "https://iisc.ac.in/", eligible_branches=["CSE", "AIML"]
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

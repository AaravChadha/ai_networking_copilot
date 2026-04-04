"""
Generate 500 diverse synthetic professional profiles.
Run once to create data/seed_profiles.json.
No API calls needed — uses random combinations from curated lists.
"""

import json
import random
from pathlib import Path

random.seed(42)

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Steven", "Ashley",
    "Andrew", "Dorothy", "Paul", "Kimberly", "Joshua", "Emily", "Kenneth", "Donna",
    "Kevin", "Michelle", "Brian", "Carol", "George", "Amanda", "Timothy", "Melissa",
    "Aisha", "Raj", "Priya", "Wei", "Yuki", "Carlos", "Fatima", "Omar",
    "Sanjay", "Mei", "Hiroshi", "Lucia", "Amir", "Zara", "Diego", "Ananya",
    "Tariq", "Yuna", "Arjun", "Sofia", "Kenji", "Nia", "Hassan", "Elena",
    "Vikram", "Camila", "Jin", "Amara", "Ravi", "Leila", "Tomas", "Ingrid",
    "Devi", "Marco", "Aaliyah", "Chen", "Sakura", "Ivan", "Nadia", "Kofi",
    "Simone", "Lars", "Deepa", "Gabriel", "Hana", "Felix", "Olga", "Kwame",
    "Mika", "Alejandro", "Thandiwe", "Nikolai", "Amina", "Rafael", "Suki", "Emeka",
    "Astrid", "Jamal", "Yoko", "Pierre", "Asha", "Dmitri", "Lina", "Mateo",
    "Chandra", "Rosa", "Idris", "Mina", "Bruno", "Akiko", "Tariq", "Freya",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Patel", "Kumar", "Singh", "Shah", "Gupta", "Sharma", "Chen", "Wang",
    "Li", "Zhang", "Liu", "Yang", "Wu", "Tanaka", "Yamamoto", "Sato",
    "Nakamura", "Watanabe", "Kim", "Park", "Choi", "Kang", "Müller", "Schmidt",
    "Fischer", "Weber", "Wagner", "Becker", "Rossi", "Russo", "Ferrari",
    "Dubois", "Laurent", "Bernard", "Moreau", "Santos", "Oliveira", "Costa",
    "Silva", "Okafor", "Adeyemi", "Mensah", "Owusu", "Ibrahim", "Hassan",
    "Ali", "Ahmed", "Mohammed", "Khan", "Johansson", "Eriksson", "Larsson",
    "Petrov", "Ivanov", "Popov", "Novak", "Horvat", "Kowalski",
]

# --- Archetype definitions ---

ARCHETYPES = {
    "university_student": {
        "weight": 80,
        "seniority": "intern",
        "roles": [
            "Computer Science Student", "MBA Candidate", "PhD Student",
            "Undergraduate Researcher", "Data Science Student", "Engineering Student",
            "Business Student", "Design Student", "Biotech Student",
            "Economics Student", "Math Student", "Physics Student",
        ],
        "companies": [
            "MIT", "Stanford University", "UC Berkeley", "Carnegie Mellon",
            "Georgia Tech", "University of Michigan", "Purdue University",
            "University of Illinois", "Cornell University", "UT Austin",
            "University of Washington", "Columbia University", "Harvard University",
            "Princeton University", "Yale University", "UCLA", "NYU",
            "University of Toronto", "ETH Zurich", "IIT Bombay",
            "University of Oxford", "Caltech", "Duke University",
        ],
        "education_suffix": "",
        "skills_pool": [
            "Python", "Java", "C++", "Machine Learning", "Data Analysis",
            "Research", "Statistics", "SQL", "TensorFlow", "React",
            "JavaScript", "Public Speaking", "Technical Writing", "Git",
            "Algorithms", "Linear Algebra", "Deep Learning", "NLP",
            "Computer Vision", "AWS", "Docker", "Figma", "Excel",
        ],
        "tags": ["student", "early-career", "research", "academic"],
    },
    "professor": {
        "weight": 40,
        "seniority": "exec",
        "roles": [
            "Professor of Computer Science", "Associate Professor of AI",
            "Assistant Professor of Data Science", "Research Professor",
            "Professor of Electrical Engineering", "Professor of Business",
            "Professor of Biomedical Engineering", "Professor of Economics",
            "Distinguished Professor", "Department Chair",
            "Professor of Machine Learning", "Professor of Robotics",
        ],
        "companies": [
            "MIT", "Stanford University", "UC Berkeley", "Carnegie Mellon",
            "Georgia Tech", "Purdue University", "University of Michigan",
            "ETH Zurich", "University of Oxford", "Harvard University",
            "Princeton University", "Caltech", "Columbia University",
            "University of Toronto", "IIT Delhi", "NUS Singapore",
        ],
        "education_suffix": " (PhD)",
        "skills_pool": [
            "Machine Learning", "Deep Learning", "Research", "Grant Writing",
            "Published Author", "Mentorship", "NLP", "Computer Vision",
            "Reinforcement Learning", "Robotics", "Data Science", "Statistics",
            "Neural Networks", "Peer Review", "Curriculum Design",
        ],
        "tags": ["academic", "research", "mentor", "expert"],
    },
    "startup_founder": {
        "weight": 60,
        "seniority": "exec",
        "roles": [
            "Founder & CEO", "Co-Founder & CTO", "Founder & COO",
            "Co-Founder & CEO", "Founding Engineer", "Solo Founder",
            "Technical Co-Founder", "Co-Founder & CPO",
        ],
        "companies": [
            "NeuralPath AI", "DataForge", "CloudNova", "QuantumLeap Tech",
            "GreenByte", "HealthStack", "FinSight AI", "AutoPilot Labs",
            "CodeCraft", "DeepSense Analytics", "RoboFlow", "Synthia AI",
            "EdgeML", "BioCompute", "PayLane", "ShipFast",
            "TrustLayer", "ScaleGrid", "FluxAI", "Nexus Robotics",
            "AgriTech Solutions", "EduVerse", "MedAI", "ClimateSense",
            "CyberShield", "FoodTech Labs", "SpaceCore", "Nuvola",
        ],
        "education_suffix": "",
        "skills_pool": [
            "Fundraising", "Product Strategy", "Leadership", "Pitch Decks",
            "Growth Hacking", "Product-Market Fit", "Team Building",
            "Business Development", "Venture Capital", "Agile", "Python",
            "System Design", "Hiring", "Go-to-Market", "Customer Discovery",
            "Revenue Growth", "Partnerships", "Startup Operations",
        ],
        "tags": ["startup", "entrepreneur", "founder", "leadership"],
    },
    "investor": {
        "weight": 35,
        "seniority": "exec",
        "roles": [
            "Partner", "Venture Partner", "Managing Director",
            "Principal", "Associate", "Investment Analyst",
            "General Partner", "Angel Investor", "Venture Capitalist",
        ],
        "companies": [
            "Andreessen Horowitz", "Sequoia Capital", "Y Combinator",
            "Accel Partners", "Benchmark", "Greylock Partners",
            "Lightspeed Venture Partners", "Index Ventures", "NEA",
            "Khosla Ventures", "Founders Fund", "GV (Google Ventures)",
            "Tiger Global", "SoftBank Vision Fund", "Bessemer Venture Partners",
            "First Round Capital", "Union Square Ventures", "Insight Partners",
            "500 Global", "Techstars", "Plug and Play",
        ],
        "education_suffix": "",
        "skills_pool": [
            "Due Diligence", "Portfolio Management", "Deal Sourcing",
            "Financial Modeling", "Valuation", "Term Sheets", "Board Membership",
            "Market Analysis", "Startup Mentorship", "Fundraising Strategy",
            "Sector Analysis", "LP Relations", "Network Building",
        ],
        "tags": ["investor", "venture-capital", "finance", "mentor"],
    },
    "software_engineer": {
        "weight": 90,
        "seniority_options": ["junior", "mid", "senior"],
        "roles": [
            "Software Engineer", "Senior Software Engineer", "Backend Engineer",
            "Frontend Engineer", "Full Stack Developer", "DevOps Engineer",
            "Platform Engineer", "Site Reliability Engineer", "Mobile Developer",
            "Cloud Engineer", "Infrastructure Engineer", "Security Engineer",
            "ML Engineer", "Data Engineer", "Software Architect",
        ],
        "companies": [
            "Google", "Meta", "Amazon", "Apple", "Microsoft", "Netflix",
            "Stripe", "Shopify", "Airbnb", "Uber", "Lyft", "DoorDash",
            "Coinbase", "Databricks", "Snowflake", "Palantir", "Figma",
            "Notion", "Discord", "Slack", "Twilio", "Cloudflare",
            "MongoDB", "Elastic", "HashiCorp", "Vercel", "Supabase",
            "Linear", "Retool", "Datadog", "Splunk", "CrowdStrike",
        ],
        "education_suffix": "",
        "skills_pool": [
            "Python", "Java", "Go", "Rust", "TypeScript", "JavaScript",
            "React", "Node.js", "AWS", "GCP", "Azure", "Kubernetes",
            "Docker", "PostgreSQL", "MongoDB", "Redis", "GraphQL",
            "REST APIs", "CI/CD", "Terraform", "System Design",
            "Microservices", "gRPC", "Kafka", "SQL", "Git",
        ],
        "tags": ["engineering", "software", "tech", "developer"],
    },
    "data_scientist": {
        "weight": 55,
        "seniority_options": ["junior", "mid", "senior"],
        "roles": [
            "Data Scientist", "Senior Data Scientist", "ML Researcher",
            "AI Research Scientist", "Applied Scientist", "Research Engineer",
            "NLP Engineer", "Computer Vision Engineer", "Data Analyst",
            "Quantitative Researcher", "AI Engineer",
        ],
        "companies": [
            "Google DeepMind", "OpenAI", "Meta AI", "Microsoft Research",
            "Amazon Science", "Apple ML", "NVIDIA", "IBM Research",
            "Anthropic", "Hugging Face", "Cohere", "Scale AI",
            "Two Sigma", "Citadel", "DE Shaw", "Renaissance Technologies",
            "Netflix", "Spotify", "Tesla", "Waymo",
        ],
        "education_suffix": "",
        "skills_pool": [
            "Python", "PyTorch", "TensorFlow", "Machine Learning", "Deep Learning",
            "NLP", "Computer Vision", "Statistics", "R", "SQL",
            "Scikit-learn", "Pandas", "NumPy", "Spark", "A/B Testing",
            "Reinforcement Learning", "LLMs", "RAG", "MLOps",
            "Feature Engineering", "Bayesian Methods", "Causal Inference",
        ],
        "tags": ["data-science", "machine-learning", "AI", "research"],
    },
    "product_manager": {
        "weight": 45,
        "seniority_options": ["mid", "senior"],
        "roles": [
            "Product Manager", "Senior Product Manager", "Group Product Manager",
            "Director of Product", "VP of Product", "Technical Product Manager",
            "Product Lead", "Head of Product",
        ],
        "companies": [
            "Google", "Meta", "Amazon", "Apple", "Microsoft", "Stripe",
            "Shopify", "Airbnb", "Uber", "Netflix", "Spotify", "Figma",
            "Notion", "Slack", "Atlassian", "Salesforce", "Adobe",
            "Intuit", "Square", "Robinhood",
        ],
        "education_suffix": "",
        "skills_pool": [
            "Product Strategy", "User Research", "A/B Testing", "Roadmapping",
            "SQL", "Data Analysis", "Agile", "Scrum", "Stakeholder Management",
            "Go-to-Market", "Prioritization", "OKRs", "Wireframing",
            "Customer Discovery", "Metrics", "Cross-functional Leadership",
        ],
        "tags": ["product", "strategy", "leadership", "tech"],
    },
    "consultant": {
        "weight": 35,
        "seniority_options": ["mid", "senior", "exec"],
        "roles": [
            "Management Consultant", "Senior Consultant", "Strategy Consultant",
            "Technology Consultant", "Partner", "Associate Partner",
            "Principal Consultant", "Director",
        ],
        "companies": [
            "McKinsey & Company", "Boston Consulting Group", "Bain & Company",
            "Deloitte", "PwC", "EY", "KPMG", "Accenture",
            "Oliver Wyman", "Roland Berger", "Kearney", "LEK Consulting",
        ],
        "education_suffix": "",
        "skills_pool": [
            "Strategy", "Data Analysis", "Presentations", "Client Management",
            "Financial Modeling", "Market Sizing", "Due Diligence",
            "Change Management", "Process Optimization", "Stakeholder Management",
            "Excel", "PowerPoint", "Problem Solving", "Business Development",
        ],
        "tags": ["consulting", "strategy", "business", "advisory"],
    },
    "designer": {
        "weight": 30,
        "seniority_options": ["junior", "mid", "senior"],
        "roles": [
            "UX Designer", "Product Designer", "Senior Product Designer",
            "UI/UX Designer", "Design Lead", "Head of Design",
            "UX Researcher", "Interaction Designer", "Visual Designer",
        ],
        "companies": [
            "Apple", "Google", "Figma", "Airbnb", "Spotify", "Meta",
            "Adobe", "Canva", "InVision", "Sketch", "Pinterest",
            "Squarespace", "Webflow", "Framer", "IDEO",
        ],
        "education_suffix": "",
        "skills_pool": [
            "Figma", "Sketch", "User Research", "Prototyping", "Wireframing",
            "Design Systems", "Typography", "Accessibility", "Usability Testing",
            "Information Architecture", "Visual Design", "Interaction Design",
            "Adobe Creative Suite", "Motion Design", "Design Thinking",
        ],
        "tags": ["design", "UX", "product", "creative"],
    },
    "executive": {
        "weight": 30,
        "seniority": "exec",
        "roles": [
            "CEO", "CTO", "CFO", "COO", "VP of Engineering",
            "VP of Sales", "VP of Marketing", "Chief Data Officer",
            "Chief Product Officer", "Chief Revenue Officer",
            "Head of Engineering", "Director of Engineering",
        ],
        "companies": [
            "Google", "Meta", "Amazon", "Microsoft", "Salesforce",
            "Adobe", "Intuit", "ServiceNow", "Workday", "HubSpot",
            "Atlassian", "Twilio", "Okta", "Palo Alto Networks",
            "Zoom", "DocuSign", "Confluent", "MongoDB",
        ],
        "education_suffix": "",
        "skills_pool": [
            "Leadership", "Strategy", "P&L Management", "Board Relations",
            "Fundraising", "M&A", "Team Building", "Scaling Organizations",
            "Executive Communication", "Vision Setting", "OKRs",
            "Cross-functional Leadership", "Investor Relations",
        ],
        "tags": ["executive", "leadership", "C-suite", "management"],
    },
}

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
    "Boston, MA", "Los Angeles, CA", "Chicago, IL", "Denver, CO",
    "Atlanta, GA", "Miami, FL", "Portland, OR", "San Diego, CA",
    "Washington, DC", "Raleigh, NC", "Nashville, TN", "Minneapolis, MN",
    "Salt Lake City, UT", "Philadelphia, PA", "Pittsburgh, PA",
    "West Lafayette, IN", "Ann Arbor, MI", "Cambridge, MA",
    "Palo Alto, CA", "Mountain View, CA", "Menlo Park, CA",
    "Toronto, Canada", "London, UK", "Berlin, Germany", "Bangalore, India",
    "Singapore", "Tel Aviv, Israel", "Sydney, Australia", "Tokyo, Japan",
    "Remote",
]

UNIVERSITIES = [
    "MIT", "Stanford University", "UC Berkeley", "Carnegie Mellon University",
    "Georgia Tech", "Purdue University", "University of Michigan",
    "University of Illinois Urbana-Champaign", "Cornell University",
    "UT Austin", "University of Washington", "Columbia University",
    "Harvard University", "Princeton University", "Yale University",
    "UCLA", "NYU", "Caltech", "Duke University", "Northwestern University",
    "University of Pennsylvania", "Brown University", "Rice University",
    "University of Toronto", "ETH Zurich", "IIT Bombay", "IIT Delhi",
    "University of Oxford", "University of Cambridge", "NUS Singapore",
]

DEGREES = ["BS", "BA", "MS", "MBA", "PhD"]


def generate_profile(archetype_name: str, archetype: dict, used_names: set) -> dict | None:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"

    # Skip duplicates
    if name in used_names:
        return None
    used_names.add(name)

    role = random.choice(archetype["roles"])
    company = random.choice(archetype["companies"])

    # Seniority
    if "seniority" in archetype:
        seniority = archetype["seniority"]
    else:
        seniority = random.choice(archetype["seniority_options"])

    # Education
    uni = random.choice(UNIVERSITIES)
    if archetype_name in ("university_student", "professor"):
        education = uni + archetype.get("education_suffix", "")
    else:
        degree = random.choice(DEGREES)
        education = f"{degree}, {uni}"

    # Skills — pick 4-7 random
    skills = random.sample(archetype["skills_pool"], min(random.randint(4, 7), len(archetype["skills_pool"])))

    # Career tags — base tags + 1-2 random extras
    extra_tags = ["networking", "mentorship", "open-to-coffee-chat", "hiring",
                  "looking-for-cofounders", "speaker", "writer", "open-source"]
    tags = archetype["tags"][:] + random.sample(extra_tags, random.randint(1, 2))

    location = random.choice(LOCATIONS)

    linkedin_url = f"https://linkedin.com/in/{first.lower()}-{last.lower()}-{random.randint(100, 999)}"

    return {
        "name": name,
        "role": role,
        "company": company,
        "education": education,
        "skills": skills,
        "career_tags": tags,
        "location": location,
        "seniority": seniority,
        "linkedin_url": linkedin_url,
    }


def main():
    # Build weighted list of archetypes
    weighted = []
    for name, arch in ARCHETYPES.items():
        weighted.extend([(name, arch)] * arch["weight"])

    profiles = []
    used_names: set[str] = set()

    while len(profiles) < 500:
        arch_name, arch = random.choice(weighted)
        profile = generate_profile(arch_name, arch, used_names)
        if profile:
            profiles.append(profile)

    # Shuffle so archetypes aren't clustered
    random.shuffle(profiles)

    output_path = Path(__file__).resolve().parent.parent / "data" / "seed_profiles.json"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(profiles, indent=2))
    print(f"Generated {len(profiles)} profiles → {output_path}")


if __name__ == "__main__":
    main()

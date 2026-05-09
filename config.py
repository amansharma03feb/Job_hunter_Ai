"""Central configuration for AI Job Hunter pipeline."""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# --- API Keys ---
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "959971760")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# --- Apify Config ---
APIFY_BASE_URL = "https://api.apify.com/v2"

# --- Target Roles ---
TARGET_TITLES = [
    "Technical Process Owner",
    "Technical Product Owner",
    "Data Platform Product Manager",
    "Platform Analyst",
    "Technical Business Analyst",
    "Product Operations",
    "Data Product Owner",
    "Senior Business Analyst",
    "Business Systems Analyst",
    "Data Governance Analyst",
    "MDM Analyst",
    "ETL Business Analyst",
    "Healthcare Business Analyst",
    "AI Business Analyst",
]

# --- Search Queries (title + location pairs) ---
SEARCH_QUERIES = [
    # Ireland
    {"title": "Technical Product Owner", "location": "Ireland"},
    {"title": "Data Product Owner", "location": "Ireland"},
    {"title": "Senior Business Analyst healthcare", "location": "Ireland"},
    {"title": "Technical Business Analyst", "location": "Ireland"},
    {"title": "Data Platform Product Manager", "location": "Ireland"},

    # United Kingdom
    {"title": "Technical Product Owner", "location": "United Kingdom"},
    {"title": "Senior Business Analyst data platform", "location": "United Kingdom"},
    {"title": "Technical Business Analyst", "location": "United Kingdom"},

    # India — global roles with travel / onsite exposure
    {"title": "Senior Business Analyst healthcare", "location": "India"},
    {"title": "Technical Product Owner", "location": "India"},
    {"title": "Data Product Owner", "location": "India"},
    {"title": "Technical Business Analyst", "location": "Bangalore"},
    {"title": "Senior Business Analyst MDM", "location": "India"},
    {"title": "Senior Business Analyst data platform", "location": "Hyderabad"},
    {"title": "Senior Business Analyst AWS Snowflake", "location": "India"},
    {"title": "Business Analyst healthcare data", "location": "Pune"},
]

# --- ATS Scoring ---
ATS_THRESHOLD = 60  # BEST FIT threshold (AI-hybrid: 20% keyword + 80% Claude)

SKILL_WEIGHTS = {
    "core_ba": {
        "weight": 3,
        "skills": [
            "business analysis", "business analyst", "stakeholder management",
            "requirements", "requirement gathering", "brd", "frd", "user stories",
            "agile", "scrum", "product owner", "product management",
            "gap analysis", "process mapping", "uat", "acceptance criteria",
        ],
    },
    "data_platform": {
        "weight": 4,
        "skills": [
            "etl", "data pipeline", "data ingestion", "kafka", "airflow",
            "snowflake", "aws", "lambda", "s3", "data warehouse",
            "data governance", "data quality", "data integration",
            "data platform", "data architecture", "data modelling",
        ],
    },
    "healthcare": {
        "weight": 4,
        "skills": [
            "healthcare", "health insurance", "hipaa", "phi", "mdm",
            "master data management", "identity resolution", "member matching",
            "claims", "clinical", "patient", "hl7", "fhir", "golden record",
        ],
    },
    "ai_ml": {
        "weight": 3,
        "skills": [
            "ai", "artificial intelligence", "machine learning", "prompt engineering",
            "chatbot", "nlp", "generative ai", "llm", "gpt", "automation",
        ],
    },
    "reporting_bi": {
        "weight": 2,
        "skills": [
            "power bi", "tableau", "microstrategy", "mstr", "sql",
            "reporting", "dashboard", "analytics", "data visualization",
            "data studio", "excel", "kpi",
        ],
    },
    "integration": {
        "weight": 3,
        "skills": [
            "api", "rest", "api integration", "json", "sftp",
            "microservices", "system integration", "middleware",
            "data contracts", "webhook",
        ],
    },
}

# --- Resume for Claude API matching ---
RESUME_SUMMARY = """
AMAN SHARMA — Senior Business Analyst | AI & Data Platforms | Healthcare Data & MDM

6+ years delivering healthcare data platforms, AI-enabled products, and enterprise ETL solutions.

CURRENT ROLE (CloudAngles, May 2024 – Present):
- Member Identity Resolution & MDM: golden record design, deterministic + probabilistic matching
  for a Fortune-class US health insurer (claims, wellness, broker, rewards, biometrics)
- ETL Pipeline Architecture: dual-mode ingestion via Kafka (real-time) + Airflow (batch) on AWS,
  50% reduction in data processing time
- API Plugin Development: REST payload contracts, on-schedule client system integration
- Snowflake Governance: table structures, data contracts, Power BI / MSTR / Tableau reporting
- Outbound Reporting: Lambda-triggered S3/SFTP delivery, multi-client bursting logic
- Production Incident Management: 79 DPIs, 5 PIs resolved maintaining SLAs
- Back-to-back 5-star ratings, two promotions in six months

PREVIOUS ROLES:
- AI Chatbot delivery via role-based prompt engineering (Algoworks)
- WMS migration .NET WinForms to XAML, Fortune 500 delivery, 98% on-time sprint delivery
- Multi-channel SaaS ad platform with demographic data integration (AdCuratio Media)
- Credit automation (40% adoption boost), B2C mobile app launch (40% revenue growth) (Aavas Financiers)

SKILLS: AWS (Kafka, Airflow, Lambda, S3), Snowflake, ETL, MDM, Identity Resolution,
HIPAA, REST API, Power BI, Tableau, MicroStrategy, SQL, Prompt Engineering, Agile/Scrum,
CSPO, BRD/FRD/SRS, UML, Stakeholder Management

EDUCATION: MBA Business Analytics (D.Y. Patil), B.Tech CS (MDU Rohtak)
CERTIFICATIONS: CSPO (Scrum Alliance), Agile & Scrum, DevOps Basics, Google Analytics, Tableau
"""

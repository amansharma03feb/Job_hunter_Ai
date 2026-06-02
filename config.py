"""Central configuration for AI Job Hunter pipeline."""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# --- API Keys ---
APIFY_TOKEN        = os.getenv("APIFY_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "959971760")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
HUNTER_API_KEY     = os.getenv("HUNTER_API_KEY", "")   # optional — 25 free/month

# --- Google Drive (OAuth2 — files owned by your Gmail, uses your storage) ---
GDRIVE_FOLDER_ID     = os.getenv("GDRIVE_FOLDER_ID", "1zOujN0Iq05l4Ld1AjUo-SU9hCGYJNPgp")
GDRIVE_CLIENT_ID     = os.getenv("GDRIVE_CLIENT_ID", "")
GDRIVE_CLIENT_SECRET = os.getenv("GDRIVE_CLIENT_SECRET", "")
GDRIVE_REFRESH_TOKEN = os.getenv("GDRIVE_REFRESH_TOKEN", "")

# --- Sender identity ---
SENDER_NAME = "Aman Sharma"

# --- Outreach limits (cost + spam control) ---
MAX_EMAILS_PER_RUN = 20  # max cold emails per daily run

# --- Job source toggles ---
ENABLE_LINKEDIN = True    # FREE via JobSpy (was Apify $$$)
ENABLE_INDEED   = True    # FREE via JobSpy (was Apify $$$)
ENABLE_NAUKRI   = True    # FREE via JobSpy (was Apify $$$)
ENABLE_REMOTE   = True    # FREE (RemoteOK public API)

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

# --- Resume summary (for ATS scoring — matches master resume PDF) ---
RESUME_SUMMARY = """
AMAN SHARMA - Sr. Business / System Analyst | US Healthcare Data | Claims - Eligibility - MDM | Snowflake - SQL - HIPAA

6+ years in the US Healthcare domain - eliciting, analysing, and documenting business and data
requirements for health insurance data platforms.

CURRENT ROLE (CloudAngles, May 2024 - Present):
- Healthcare Data Requirements & BRD/FRD: BRDs, functional requirements, data requirement documents,
  field definitions, transformation logic, business rules for high-volume health insurance data platforms
- SQL-Based Data Analysis & Validation (Snowflake): source-to-target reconciliation, row count
  comparisons, null rate analysis, join integrity validation across healthcare data tables
- Healthcare Claims & Eligibility Data Analysis: claims processing, member eligibility and enrolment,
  wellness programme data, broker channel data, biometric records
- Member Identity Resolution & MDM: golden record, deterministic + probabilistic matching,
  Master Member ID across claims, eligibility, wellness, broker, rewards, biometrics
- HIPAA Compliance & PHI Governance: PHI field-level classification, access-tier definitions,
  minimum necessary standards, audit trail requirements
- ETL Pipeline Requirements: dual-mode ingestion Kafka (real-time) + Airflow (batch) on AWS,
  50% data processing time reduction, REST API integration specs
- Snowflake Data Warehouse Governance: table structures, data contracts, field naming standards,
  MSTR, Power BI reporting layers
- UAT & Data Reconciliation: 79 DPIs, 5 PIs resolved maintaining SLAs
- Back-to-back 5-star ratings, two promotions within six months

PREVIOUS ROLES:
- AI Chatbot BA + Product Owner, WMS migration .NET to XAML, Power BI dashboards (Algoworks)
- Multi-channel SaaS ad platform, Experian data integration (AdCuratio Media)
- Credit automation, B2C mobile app, KYC compliance (Aavas Financiers)

SKILLS: US Healthcare Data, Claims, Eligibility, MDM, Identity Resolution, HIPAA, PHI,
Snowflake, SQL, AWS (Kafka, Airflow, Lambda, S3), ETL, Data Governance, BRD, FRD,
Power BI, MicroStrategy, Tableau, REST API, Agile, Scrum, CSPO, JIRA, Confluence

EDUCATION: MBA Business Analytics (D.Y. Patil 2023-2025), B.Tech CS (MDU Rohtak 2015-2019)
CERTIFICATIONS: CSPO (Scrum Alliance), Agile & Scrum, DevOps Basics, Google Analytics, Tableau
"""

# --- Full resume text (for tailoring + cover letter generation) ---
RESUME_FULL = """
AMAN SHARMA
Email: amansharma03feb@gmail.com | LinkedIn: linkedin.com/in/amansharma03feb
Location: India (open to relocate: Ireland / UK / EU)

PROFESSIONAL SUMMARY
Senior Business Analyst with 6+ years of experience delivering healthcare data platforms,
AI-enabled products, and enterprise ETL/MDM solutions. Proven track record bridging business
and engineering teams across US healthcare, fintech, logistics, and SaaS domains.
Seeking Senior BA / Technical Product Owner roles in Ireland, UK, or global India teams with travel exposure.

EXPERIENCE

Senior Business Analyst — CloudAngles (May 2024 – Present)
Client: Fortune-class US Health Insurance Company
- Designed and owned Member Identity Resolution & MDM platform: golden record architecture
  using deterministic + probabilistic matching across claims, wellness, broker, rewards, and biometrics data
- Architected dual-mode ETL ingestion pipeline: Kafka (real-time streaming) + Airflow (batch) on AWS;
  delivered 50% reduction in data processing time
- Authored REST API payload contracts for 8+ plugin integrations with downstream client systems;
  coordinated on-schedule delivery across 3 time zones
- Governed Snowflake data structures, data contracts, and multi-tenant table design;
  enabled Power BI, MicroStrategy, and Tableau reporting layers
- Built Lambda-triggered outbound reporting: S3/SFTP delivery with multi-client bursting logic
- Resolved 79 Data Processing Incidents (DPIs) and 5 Priority Incidents (PIs) maintaining 99.8% SLA
- Received back-to-back 5-star client ratings; promoted twice within six months

Business Analyst — Algoworks (Jan 2023 – Apr 2024)
- Led AI chatbot delivery for enterprise client; designed role-based prompt engineering framework
  reducing average handle time by 35%
- Delivered WMS migration from .NET WinForms to XAML for Fortune 500 retail client;
  98% on-time sprint delivery across 12 sprints
- Produced BRDs, FRDs, SRS documents, and UML diagrams for 4 concurrent product streams

Business Analyst — AdCuratio Media (Jun 2021 – Dec 2022)
- Built requirements and delivery for multi-channel SaaS ad platform integrating demographic data APIs
- Managed stakeholder alignment across product, engineering, and sales for 3 major feature releases

Business Analyst — Aavas Financiers (Jul 2019 – May 2021)
- Automated credit underwriting workflow; drove 40% boost in digital adoption
- Led B2C mobile app launch end-to-end; contributed to 40% revenue growth in digital channel

EDUCATION
MBA — Business Analytics, D.Y. Patil University (2019)
B.Tech — Computer Science, MDU Rohtak (2017)

CERTIFICATIONS
- Certified Scrum Product Owner (CSPO) — Scrum Alliance
- Agile & Scrum Professional
- Google Analytics Certified
- Tableau Desktop Specialist
- DevOps Basics

SKILLS
Domain:      Healthcare Data, MDM, Identity Resolution, HIPAA/PHI, Claims Processing, Fintech
Data & ETL:  AWS (Kafka, Airflow, Lambda, S3), Snowflake, ETL Pipelines, Data Governance
BA Tools:    BRD/FRD/SRS, User Stories, Agile/Scrum, UAT, Gap Analysis, Process Mapping, UML
Reporting:   Power BI, Tableau, MicroStrategy, SQL, Excel
Integration: REST API, JSON, SFTP, Microservices, Data Contracts
AI:          Prompt Engineering, Generative AI, LLM workflows, Chatbot delivery
"""

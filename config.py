"""Central configuration for AI Job Hunter pipeline."""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# --- Cost control ---
# Set FREE_MODE=true in .env to disable ALL paid APIs (Claude, Apollo, Apify)
# Pipeline runs on keyword scoring + free website scraping only
FREE_MODE = os.getenv("FREE_MODE", "false").lower() == "true"

# --- API Keys (disabled when FREE_MODE=true) ---
APIFY_TOKEN        = "" if FREE_MODE else os.getenv("APIFY_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "959971760")
ANTHROPIC_API_KEY  = "" if FREE_MODE else os.getenv("ANTHROPIC_API_KEY", "")
GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
HUNTER_API_KEY     = os.getenv("HUNTER_API_KEY", "")   # optional — 25 free/month
APOLLO_API_KEY     = "" if FREE_MODE else os.getenv("APOLLO_API_KEY", "")

# --- Google Drive (OAuth2 — files owned by your Gmail, uses your storage) ---
GDRIVE_FOLDER_ID     = os.getenv("GDRIVE_FOLDER_ID", "1zOujN0Iq05l4Ld1AjUo-SU9hCGYJNPgp")
GDRIVE_CLIENT_ID     = os.getenv("GDRIVE_CLIENT_ID", "")
GDRIVE_CLIENT_SECRET = os.getenv("GDRIVE_CLIENT_SECRET", "")
GDRIVE_REFRESH_TOKEN = os.getenv("GDRIVE_REFRESH_TOKEN", "")

# --- Sender identity ---
SENDER_NAME = "Aman Sharma"

# --- Outreach limits (cost + spam control) ---
MAX_EMAILS_PER_RUN = 40  # max cold emails per daily run
FOLLOWUP_AFTER_DAYS = 5  # send follow-up if no reply after N days

# --- Job source toggles ---
ENABLE_LINKEDIN      = True    # FREE via JobSpy + Apify fallback
ENABLE_INDEED        = False   # 403 from India IPs — enable with VPN/proxy
ENABLE_ZIPRECRUITER  = False   # 403 from India IPs — enable with VPN/proxy
ENABLE_REMOTE        = True    # FREE (RemoteOK public API)

# --- Apify Config ---
APIFY_BASE_URL = "https://api.apify.com/v2"

# --- Target Roles (Healthcare + AI/AdTech) ---
TARGET_TITLES = [
    # Healthcare / Data Platform
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
    # AI / AdTech domain — BA & PO roles only
    "AI Business Analyst",
    "AI Product Analyst",
    "AI Product Owner",
    "AI Solutions Analyst",
    "AI Operations Analyst",
    "AdTech Business Analyst",
    "Product Owner AI",
    "Business Analyst Machine Learning",
]

# --- Search Queries (title + location pairs) ---
SEARCH_QUERIES = [
    # ═══ Ireland ═══
    {"title": "Technical Product Owner", "location": "Ireland"},
    {"title": "Data Product Owner", "location": "Ireland"},
    {"title": "Senior Business Analyst healthcare", "location": "Ireland"},
    {"title": "Technical Business Analyst", "location": "Ireland"},
    {"title": "Data Platform Product Manager", "location": "Ireland"},
    {"title": "AI Business Analyst", "location": "Ireland"},
    {"title": "AI Product Owner", "location": "Ireland"},
    {"title": "Business Analyst AI machine learning", "location": "Ireland"},

    # ═══ United Kingdom ═══
    {"title": "Technical Product Owner", "location": "United Kingdom"},
    {"title": "Senior Business Analyst data platform", "location": "United Kingdom"},
    {"title": "Technical Business Analyst", "location": "United Kingdom"},
    {"title": "AI Business Analyst", "location": "United Kingdom"},
    {"title": "Business Analyst generative AI", "location": "United Kingdom"},
    {"title": "Product Owner AI", "location": "United Kingdom"},

    # ═══ EU / Remote ═══
    {"title": "AI Business Analyst", "location": "Germany"},
    {"title": "Business Analyst AI", "location": "Netherlands"},
    {"title": "AI Product Owner", "location": "Europe"},

    # ═══ UAE / Dubai ═══
    {"title": "Senior Business Analyst", "location": "Dubai"},
    {"title": "Technical Product Owner", "location": "UAE"},
    {"title": "AI Business Analyst", "location": "Dubai"},
    {"title": "Data Product Owner", "location": "UAE"},
    {"title": "Business Analyst healthcare", "location": "Dubai"},
    {"title": "AI Product Owner", "location": "UAE"},

    # ═══ India (global companies, travel/relocation potential) ═══
    {"title": "Senior Business Analyst healthcare", "location": "India"},
    {"title": "Technical Product Owner", "location": "India"},
    {"title": "Data Product Owner", "location": "India"},
    {"title": "Technical Business Analyst", "location": "Bangalore"},
    {"title": "Senior Business Analyst MDM", "location": "India"},
    {"title": "AI Business Analyst", "location": "India"},
    {"title": "Business Analyst AI LLM", "location": "Bangalore"},
    {"title": "AI Product Owner", "location": "India"},
    {"title": "Business Analyst generative AI", "location": "India"},
    {"title": "Senior Business Analyst data platform", "location": "Hyderabad"},
    {"title": "Senior Business Analyst AWS Snowflake", "location": "India"},
    {"title": "Business Analyst AdTech", "location": "India"},
]

# --- ATS Scoring ---
ATS_THRESHOLD = 45  # BEST FIT threshold — lowered to increase outreach volume

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
        "weight": 4,
        "skills": [
            "ai", "artificial intelligence", "machine learning", "prompt engineering",
            "chatbot", "nlp", "generative ai", "llm", "gpt", "automation",
            "rag", "retrieval augmented", "agentic", "langgraph", "langchain",
            "ai product", "ai native", "ai solutions", "openai", "claude",
            "vector database", "embeddings", "fine-tuning", "ai validation",
        ],
    },
    "adtech_media": {
        "weight": 2,
        "skills": [
            "adtech", "ad tech", "advertising", "addressable tv", "audience targeting",
            "ad delivery", "campaign", "media", "programmatic", "dsp", "ssp",
            "ad inventory", "ad sales", "forecasting", "pricing model",
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
Seeking Senior BA / Technical Product Owner roles in Ireland, UK, UAE, or global India teams with travel exposure.

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

# --- AI Resume summary (for AI/AdTech jobs — second resume) ---
AI_RESUME_SUMMARY = """
AMAN SHARMA - AI-Native Business Analyst · AdTech & Media · Agentic AI & RAG Applications

6+ years as an AI-Native BA who goes beyond documentation — building working RAG applications,
agentic AI prototypes, and AI-generated UI mockups. Hands-on across the full AI-native BA toolkit:
LangGraph-orchestrated agentic workflows, RAG pipeline architecture, state management, tool access
patterns, external memory design, and prompt engineering.

CURRENT ROLE (CloudAngles, May 2024 - Present):
- Applied AI-native approach to MDM decision review — LangGraph-orchestrated agentic workflows
  (candidate ingestion → confidence scoring → auto-merge gate → steward review → audit memo),
  RAG-based operational Q&A, state management, tool access patterns, PII masking layers
- Led member identity resolution (MDM) — deterministic + probabilistic matching
- UAT, data validation, Snowflake source-to-target reconciliation, 79 production data issues resolved
- Back-to-back 5-star ratings; two promotions within six months

PREVIOUS ROLES:
- AI Chatbot BA + Product Owner: GPT-4 RAG sales intelligence chatbot, Airtable knowledge base,
  prompt engineering (role-based, constraint design, few-shot), Gemini Q&A validation (Algoworks)
- AdTech BA: Multi-channel addressable TV platform, audience targeting, ad delivery predictor,
  Experian demographic integration, Tableau dashboards (AdCuratio Media)
- BA: Credit automation, B2C mobile app, KYC compliance, Razorpay (Aavas Financiers)

SKILLS: Agentic AI, RAG Pipeline, LangGraph, Prompt Engineering, AI Mockups, AI Validation,
Ad Sales, Audience Targeting, Pricing Optimization, Forecasting Models,
Snowflake, SQL, AWS, ETL, BRD/FRD, Agile, Scrum, CSPO, Power BI, Tableau, MSTR
"""

# --- AI keywords for resume selection ---
AI_JOB_KEYWORDS = [
    "ai ", "artificial intelligence", "machine learning", "generative ai", "gen ai",
    "llm", "gpt", "rag", "retrieval augmented", "agentic", "langgraph", "langchain",
    "prompt engineer", "nlp", "natural language", "chatbot", "ai product",
    "ai native", "ai solution", "adtech", "ad tech", "advertising technology",
    "addressable", "audience targeting", "programmatic", "media tech",
]

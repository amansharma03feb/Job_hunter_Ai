TARGET_ROLES = [
    "business analyst",
    "senior business analyst",
    "technical business analyst",
    "business systems analyst",
    "data analyst",
    "senior data analyst",
    "data platform analyst",
    "product analyst",
    "product owner",
    "data product owner",
    "analytics consultant",
    "data governance",
    "mdm analyst",
    "etl analyst",
    "bi analyst",
    "healthcare analyst",
    "ai business analyst",
    "analytics transformation",
    "business intelligence analyst",
]

TARGET_CATEGORIES = [
    "data",
    "business",
    "product",
    "analyst",
    "qa",
    "software dev",
    "all others",
]

TARGET_LOCATIONS = [
    "ireland",
    "united kingdom",
    "uk",
    "germany",
    "netherlands",
    "eu",
    "europe",
    "dubai",
    "uae",
    "singapore",
    "remote",
]

VISA_KEYWORDS = [
    "visa sponsorship",
    "sponsorship available",
    "relocation support",
    "relocation assistance",
    "work permit",
    "global mobility",
    "visa provided",
    "critical skills",
    "skilled worker",
    "eu blue card",
    "international candidates",
    "open to all nationalities",
]

# Weighted skill categories for smarter ATS scoring
SKILL_WEIGHTS = {
    "core_domain": {
        "weight": 3,
        "skills": [
            "business analysis", "business analyst", "stakeholder management",
            "requirement gathering", "requirements", "brd", "frd", "user stories",
            "agile", "scrum", "product owner", "uml", "gap analysis",
        ],
    },
    "data_engineering": {
        "weight": 3,
        "skills": [
            "etl", "data pipeline", "data ingestion", "kafka", "airflow",
            "snowflake", "aws", "lambda", "s3", "data warehouse",
            "data governance", "data quality", "data integration",
        ],
    },
    "healthcare_domain": {
        "weight": 4,
        "skills": [
            "healthcare", "health insurance", "hipaa", "phi", "mdm",
            "master data management", "identity resolution", "member matching",
            "claims", "clinical", "patient", "hl7", "fhir",
        ],
    },
    "ai_analytics": {
        "weight": 2,
        "skills": [
            "ai", "artificial intelligence", "machine learning", "prompt engineering",
            "chatbot", "nlp", "generative ai", "llm",
        ],
    },
    "reporting_bi": {
        "weight": 2,
        "skills": [
            "power bi", "tableau", "microstrategy", "mstr", "sql",
            "reporting", "dashboard", "data studio", "analytics",
            "data visualization", "excel",
        ],
    },
    "api_integration": {
        "weight": 2,
        "skills": [
            "api", "rest", "api integration", "json", "sftp",
            "microservices", "system integration",
        ],
    },
}

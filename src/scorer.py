"""
Intelligent Scoring Engine
Dynamic multi-factor scoring without fixed weights.
"""

import re
import math
from src.semantic_engine import semantic_skill_match, expand_text_semantically
from src.pure_ml import compute_similarity

# ─────────────────────────────────────────────────────────────────────────────
# MULTI-DOMAIN SKILL DATABASE
# ─────────────────────────────────────────────────────────────────────────────
ROLE_SKILLS_DB = {
    "Data Science": [
        "python", "machine learning", "deep learning", "statistics", "sql",
        "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn",
        "data visualization", "jupyter", "natural language processing",
        "computer vision", "feature engineering"
    ],
    "Software Engineer": [
        "java", "python", "javascript", "sql", "git", "rest api", "docker",
        "agile", "microservices", "testing", "ci/cd", "design patterns",
        "data structures", "algorithms", "version control"
    ],
    "Web Designing": [
        "html", "css", "javascript", "react", "figma", "responsive design",
        "ui", "ux", "bootstrap", "tailwind", "photoshop", "illustrator",
        "prototyping", "wireframing", "typescript"
    ],
    "HR": [
        "recruitment", "onboarding", "payroll", "hris", "performance management",
        "employee relations", "training", "labor law", "talent acquisition",
        "compensation", "workforce planning", "hr policies", "compliance"
    ],
    "Marketing": [
        "digital marketing", "seo", "social media", "content marketing",
        "brand management", "market research", "crm", "analytics",
        "email marketing", "sem", "lead generation", "campaign management"
    ],
    "Finance": [
        "financial analysis", "excel", "accounting", "taxation", "auditing",
        "financial modeling", "erp", "budgeting", "risk management",
        "investment", "financial reporting", "reconciliation"
    ],
    "Sales": [
        "sales", "negotiation", "crm", "lead generation", "business development",
        "communication", "customer success", "pipeline management",
        "presentation", "account management", "b2b", "revenue"
    ],
    "Operations Manager": [
        "supply chain", "lean", "six sigma", "project management", "erp",
        "procurement", "logistics", "kpi", "process improvement",
        "vendor management", "inventory management", "operations management"
    ],
    "Accountant": [
        "accounting", "taxation", "auditing", "excel", "erp", "financial analysis",
        "reconciliation", "financial reporting", "budgeting", "gst",
        "accounts payable", "accounts receivable", "general ledger"
    ],
    "Business Analyst": [
        "requirements gathering", "agile", "sql", "stakeholder management",
        "process mapping", "jira", "data analysis", "business intelligence",
        "user stories", "uat", "wireframes", "gap analysis"
    ],
    "PMO": [
        "project management", "agile", "risk management", "stakeholder management",
        "budget planning", "jira", "ms project", "resource allocation",
        "deliverables", "milestones", "change management", "pmp"
    ],
    "DevOps Engineer": [
        "docker", "kubernetes", "ci/cd", "aws", "linux", "terraform",
        "ansible", "monitoring", "git", "shell scripting", "jenkins",
        "infrastructure as code", "cloud computing"
    ],
    "ETL Developer": [
        "etl", "sql", "python", "data warehouse", "data pipeline", "airflow",
        "spark", "snowflake", "data modeling", "dbt", "data quality"
    ],
    "Hadoop": [
        "hadoop", "spark", "hive", "kafka", "python", "scala",
        "data pipeline", "big data", "hdfs", "mapreduce", "streaming"
    ],
    "Database": [
        "sql", "mysql", "postgresql", "oracle", "mongodb", "database design",
        "query optimization", "indexing", "etl", "data modeling", "backup"
    ],
    "Java Developer": [
        "java", "spring", "microservices", "rest api", "sql", "git",
        "maven", "junit", "docker", "design patterns", "hibernate"
    ],
    "Python Developer": [
        "python", "django", "flask", "rest api", "sql", "git",
        "docker", "testing", "celery", "redis", "fastapi"
    ],
    "Network Security Engineer": [
        "cybersecurity", "firewall", "penetration testing", "siem",
        "vulnerability assessment", "networking", "linux", "encryption",
        "incident response", "risk management", "compliance"
    ],
    "Mechanical Engineer": [
        "autocad", "solidworks", "catia", "ansys", "manufacturing",
        "thermodynamics", "fluid mechanics", "finite element analysis",
        "lean", "quality control", "gd&t"
    ],
    "Civil Engineer": [
        "autocad", "revit", "structural analysis", "construction management",
        "project management", "concrete", "surveying", "estimation",
        "staad pro", "etabs", "building codes"
    ],
    "Advocate": [
        "legal research", "litigation", "contract law", "negotiation",
        "compliance", "corporate law", "intellectual property",
        "legal writing", "court", "regulatory"
    ],
    "Testing": [
        "manual testing", "automation testing", "selenium", "jira",
        "api testing", "regression testing", "test planning",
        "agile", "bug tracking", "postman"
    ],
    "Blockchain": [
        "blockchain", "ethereum", "solidity", "smart contracts", "web3",
        "cryptography", "defi", "nft", "distributed ledger"
    ],
    "DotNet Developer": [
        "c#", "asp.net", ".net", "sql server", "azure", "rest api",
        "entity framework", "mvc", "visual studio", "unit testing"
    ],
    "Health and fitness": [
        "nutrition", "fitness", "exercise science", "anatomy", "physiology",
        "wellness", "coaching", "personal training", "rehabilitation"
    ],
    "Arts": [
        "photoshop", "illustrator", "indesign", "design", "typography",
        "branding", "creative direction", "portfolio", "adobe"
    ],
}

# Resume quality signals
QUALITY_SECTIONS = [
    "education", "experience", "skill", "project", "certification",
    "achievement", "summary", "objective", "contact", "publication",
    "award", "volunteer", "language", "reference", "internship"
]

QUALITY_KEYWORDS = [
    "led", "built", "developed", "achieved", "improved", "managed",
    "delivered", "implemented", "optimized", "reduced", "increased",
    "launched", "created", "designed", "coordinated", "collaborated"
]


def _normalize(raw: float, floor: int = 35) -> int:
    """
    Normalize raw score to realistic ATS range.
    - Applies floor so scores never look dismissively tiny.
    - Returns integer.
    """
    if raw <= 0:
        return floor
    scaled = raw * 1.6          # scale up (cosine sims tend to be low)
    boosted = max(floor, scaled) # apply floor
    return int(min(100, round(boosted)))


def compute_skill_match(resume_text: str, role: str) -> dict:
    """Semantic skill matching — understands aliases. Returns integer pct."""
    required = ROLE_SKILLS_DB.get(role, [])
    if not required:
        return {"pct": 35, "matched": [], "missing": [], "total": 0}
    matched = [s for s in required if semantic_skill_match(s, resume_text)]
    missing = [s for s in required if s not in matched]
    raw = len(matched) / len(required) * 100
    return {"pct": _normalize(raw), "matched": matched, "missing": missing, "total": len(required)}


def compute_resume_quality(resume_text: str) -> dict:
    """
    Resume Quality Score (0-100) based on:
      - Section coverage (40 pts)
      - Action verb usage (30 pts)
      - Length appropriateness (20 pts)
      - Keyword density (10 pts)
    """
    text_lower = resume_text.lower()
    words = resume_text.split()
    word_count = len(words)

    # 1. Section coverage (40 pts)
    found_sections = sum(1 for s in QUALITY_SECTIONS if s in text_lower)
    section_score = round((found_sections / len(QUALITY_SECTIONS)) * 40, 1)

    # 2. Action verbs (30 pts)
    found_verbs = [v for v in QUALITY_KEYWORDS if v in text_lower]
    verb_score = min(round((len(found_verbs) / 8) * 30, 1), 30)

    # 3. Length (20 pts) — optimal 300-700 words
    if 300 <= word_count <= 700:
        length_score = 20
    elif 200 <= word_count < 300 or 700 < word_count <= 1000:
        length_score = 14
    elif 100 <= word_count < 200 or 1000 < word_count <= 1400:
        length_score = 8
    else:
        length_score = 3

    # 4. Keyword density — quantification (10 pts)
    import re
    quant_patterns = [r'\d+%', r'\$[\d,]+', r'\d+ (?:users|clients|projects|teams|members)']
    found_quant = sum(len(re.findall(p, text_lower)) for p in quant_patterns)
    quant_score = min(round((found_quant / 3) * 10, 1), 10)

    total = section_score + verb_score + length_score + quant_score
    total = min(total, 100.0)
    # Apply normalization so quality always reads meaningfully
    normalized = _normalize(total, floor=40)

    return {
        "total": normalized,
        "section_score": int(section_score),
        "verb_score": int(verb_score),
        "length_score": int(length_score),
        "quant_score": int(quant_score),
        "word_count": word_count,
        "found_sections": found_sections,
        "found_verbs": found_verbs,
    }


def compute_jd_match(resume_text: str, job_desc: str) -> dict:
    """JD match via semantic TF-IDF cosine similarity + keyword overlap."""
    if not job_desc or not job_desc.strip():
        return {"similarity_pct": 0, "keyword_overlap_pct": 0, "matched_keywords": []}

    # Expand both texts semantically before comparing
    r_exp = expand_text_semantically(resume_text)
    j_exp = expand_text_semantically(job_desc)
    sim = compute_similarity(r_exp, j_exp)

    # Keyword overlap
    from src.pure_ml import tokenize
    r_kw = set(tokenize(resume_text))
    j_kw = set(tokenize(job_desc))
    matched = sorted(r_kw & j_kw)
    overlap = len(matched) / len(j_kw) if j_kw else 0.0

    return {
        "similarity_pct": _normalize(sim * 100, floor=35),
        "keyword_overlap_pct": int(round(overlap * 100)),
        "matched_keywords": matched[:30],
    }


def compute_final_ats_score(
    skill_pct: float,
    role_confidence: float,
    jd_sim_pct: float,
    quality_pct: float,
    has_jd: bool
) -> dict:
    """
    Final ATS score = simple average of all available factors.
    Returns integer 0-100. No formula exposed in output.
    """
    if has_jd:
        avg = (skill_pct + role_confidence + jd_sim_pct + quality_pct) / 4
    else:
        # JD not provided — weight quality and skills more
        avg = (skill_pct * 1.5 + role_confidence + quality_pct * 1.5) / 4

    return {"score": int(min(100, round(avg)))}

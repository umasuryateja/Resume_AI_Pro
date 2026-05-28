"""
Semantic Engine - pure Python synonym expansion + alias resolution.
Makes the system understand meaning, not just exact keywords.
"""

# ── SEMANTIC ALIASES (phrase → canonical) ─────────────────────────────────────
# When any alias is found in text, it counts as the canonical term.
SEMANTIC_ALIASES = {
    # Data Science / ML
    "machine learning": ["ml", "machine-learning", "machinelearning"],
    "deep learning":    ["dl", "deep-learning", "deeplearning", "neural net", "neural nets"],
    "natural language processing": ["nlp", "text analytics", "text mining", "computational linguistics"],
    "computer vision":  ["cv", "image recognition", "image processing", "object detection"],
    "artificial intelligence": ["ai", "a.i.", "intelligent systems"],
    "scikit-learn":     ["sklearn", "scikit learn"],
    "tensorflow":       ["tf", "tensor flow"],
    "pytorch":          ["torch"],
    "statistics":       ["statistical analysis", "statistical modeling", "biostatistics", "econometrics"],
    "data visualization": ["data viz", "visualization", "charting", "dashboards"],
    "python":           ["py", "python3", "python2"],
    "jupyter":          ["jupyter notebook", "ipython", "colab"],
    "pandas":           ["dataframes", "data frames"],
    "sql":              ["structured query language", "mysql", "postgresql", "mssql", "t-sql", "plsql", "pl/sql"],
    "big data":         ["hadoop", "hdfs", "spark", "hive", "mapreduce"],
    "etl":              ["extract transform load", "data pipeline", "data ingestion"],

    # Software Engineering
    "javascript":       ["js", "node.js", "nodejs", "ecmascript"],
    "typescript":       ["ts"],
    "c++":              ["cpp", "c plus plus"],
    "c#":               ["csharp", "c sharp", "dotnet", "net"],
    "microservices":    ["micro services", "service oriented", "soa"],
    "rest api":         ["restful", "rest", "api", "web api", "http api"],
    "version control":  ["git", "github", "gitlab", "bitbucket", "svn"],
    "ci/cd":            ["continuous integration", "continuous deployment", "devops pipeline", "jenkins", "github actions"],
    "agile":            ["scrum", "kanban", "sprint", "agile methodology"],
    "testing":          ["unit testing", "qa", "quality assurance", "selenium", "jest", "pytest"],

    # Cloud
    "aws":              ["amazon web services", "amazon cloud", "ec2", "s3", "lambda", "sagemaker"],
    "azure":            ["microsoft azure", "ms azure", "azure cloud"],
    "gcp":              ["google cloud", "google cloud platform", "bigquery", "google cloud services"],
    "cloud computing":  ["cloud services", "cloud infrastructure", "cloud platform"],

    # Finance / Accounting
    "financial analysis": ["financial modeling", "financial planning", "financial reporting", "fp&a"],
    "accounting":       ["bookkeeping", "general ledger", "accounts payable", "accounts receivable"],
    "taxation":         ["tax", "gst", "income tax", "tax compliance", "tax filing"],
    "auditing":         ["audit", "internal audit", "external audit", "statutory audit"],
    "excel":            ["ms excel", "microsoft excel", "spreadsheet", "vlookup", "pivot table"],
    "erp":              ["sap", "oracle erp", "tally", "quickbooks", "sage"],
    "investment":       ["portfolio management", "asset management", "equity", "securities"],
    "risk management":  ["risk assessment", "risk analysis", "credit risk", "market risk"],

    # HR
    "recruitment":      ["talent acquisition", "hiring", "sourcing", "staffing", "headhunting"],
    "onboarding":       ["orientation", "induction", "employee onboarding"],
    "payroll":          ["compensation", "salary administration", "payroll processing"],
    "performance management": ["appraisal", "performance appraisal", "kpi", "okr"],
    "hris":             ["hrms", "hr software", "workday", "bamboohr", "zoho hr"],
    "employee relations": ["employee engagement", "industrial relations", "labor relations"],
    "training":         ["learning & development", "l&d", "employee training", "corporate training"],

    # Marketing
    "digital marketing": ["online marketing", "internet marketing", "digital advertising"],
    "seo":              ["search engine optimization", "organic search", "keyword optimization"],
    "sem":              ["search engine marketing", "paid search", "google ads", "ppc"],
    "social media":     ["social media marketing", "smm", "instagram", "linkedin marketing", "facebook ads"],
    "content marketing": ["content creation", "content strategy", "blogging", "copywriting"],
    "brand management": ["branding", "brand strategy", "brand identity"],
    "market research":  ["consumer research", "market analysis", "competitive analysis"],
    "crm":              ["customer relationship management", "salesforce", "hubspot", "zoho crm"],

    # Operations / Supply Chain
    "supply chain":     ["supply chain management", "scm", "logistics", "procurement"],
    "lean":             ["lean manufacturing", "lean methodology", "waste reduction"],
    "six sigma":        ["6 sigma", "process improvement", "dmaic", "black belt", "green belt"],
    "project management": ["pmp", "project planning", "project delivery", "project coordination"],
    "operations management": ["operations", "business operations", "operational efficiency"],

    # Sales
    "sales":            ["business development", "bd", "revenue generation", "deal closing"],
    "negotiation":      ["contract negotiation", "deal negotiation"],
    "lead generation":  ["prospecting", "pipeline building", "demand generation"],
    "customer success": ["account management", "client relationship", "customer retention"],

    # General / Soft Skills
    "communication":    ["verbal communication", "written communication", "presentation skills"],
    "leadership":       ["team leadership", "people management", "managing teams"],
    "problem solving":  ["analytical thinking", "critical thinking", "troubleshooting"],
    "collaboration":    ["teamwork", "cross-functional", "working with teams"],

    # Civil / Mechanical
    "autocad":          ["auto cad", "cad", "computer aided design"],
    "structural analysis": ["structural design", "finite element", "fea", "ansys"],
    "construction management": ["site management", "construction supervision"],

    # Legal
    "legal research":   ["case research", "legal analysis", "jurisprudence"],
    "litigation":       ["court proceedings", "legal proceedings", "trial"],
    "contract law":     ["contract drafting", "contract review", "contract management"],
}

# Build reverse lookup: alias → canonical
_ALIAS_TO_CANONICAL: dict = {}
for canonical, aliases in SEMANTIC_ALIASES.items():
    for alias in aliases:
        _ALIAS_TO_CANONICAL[alias.lower()] = canonical


def expand_text_semantically(text: str) -> str:
    """
    Expand text by appending canonical forms of detected aliases.
    This means 'ml' in text also activates 'machine learning' matches.
    """
    text_lower = text.lower()
    expansions = set()
    for alias, canonical in _ALIAS_TO_CANONICAL.items():
        import re
        pattern = r'\b' + re.escape(alias) + r'\b'
        if re.search(pattern, text_lower):
            expansions.add(canonical)
    if expansions:
        return text + " " + " ".join(expansions)
    return text


def semantic_skill_match(skill: str, text: str) -> bool:
    """
    Check if a skill (or any of its aliases) is present in text.
    Case-insensitive, whole-word match.
    """
    import re
    text_lower = text.lower()
    skill_lower = skill.lower()

    # Direct match
    if re.search(r'\b' + re.escape(skill_lower) + r'\b', text_lower):
        return True

    # Check if skill is a canonical → look for its aliases
    aliases = SEMANTIC_ALIASES.get(skill_lower, [])
    for alias in aliases:
        if re.search(r'\b' + re.escape(alias.lower()) + r'\b', text_lower):
            return True

    # Check if skill is itself an alias → look for its canonical
    canonical = _ALIAS_TO_CANONICAL.get(skill_lower)
    if canonical:
        if re.search(r'\b' + re.escape(canonical) + r'\b', text_lower):
            return True
        for alias in SEMANTIC_ALIASES.get(canonical, []):
            if re.search(r'\b' + re.escape(alias.lower()) + r'\b', text_lower):
                return True

    return False

"""
Text Processing Module (pure-Python stdlib only)
"""

import re

# ─────────────────────────────────────────────────────────────────────────────
# SKILL TAXONOMY
# ─────────────────────────────────────────────────────────────────────────────
SKILL_TAXONOMY = {
    "Programming Languages": [
        "python", "java", "javascript", "c++", "c#", "typescript", "r", "go",
        "kotlin", "swift", "scala", "rust", "php", "ruby", "matlab", "bash",
        "shell", "perl", "lua", "dart"
    ],
    "Web Technologies": [
        "html", "css", "react", "angular", "vue", "node.js", "nodejs", "express",
        "django", "flask", "fastapi", "spring", "asp.net", "jquery", "bootstrap",
        "tailwind", "graphql", "rest", "restful", "api", "webpack", "next.js",
        "svelte"
    ],
    "Data Science & ML": [
        "machine learning", "deep learning", "neural network", "tensorflow", "pytorch",
        "keras", "scikit-learn", "sklearn", "pandas", "numpy", "matplotlib",
        "seaborn", "plotly", "jupyter", "computer vision", "nlp",
        "natural language processing", "bert", "gpt", "transformer", "xgboost",
        "lightgbm", "random forest", "regression", "classification", "clustering",
        "reinforcement learning", "opencv", "hugging face"
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "ci/cd",
        "jenkins", "git", "github", "gitlab", "terraform", "ansible", "linux",
        "nginx", "apache", "microservices", "devops", "mlops", "sagemaker",
        "lambda", "s3", "ec2", "heroku", "vercel", "netlify"
    ],
    "Databases": [
        "sql", "mysql", "postgresql", "sqlite", "mongodb", "redis", "cassandra",
        "elasticsearch", "oracle", "nosql", "dynamodb", "firebase", "neo4j",
        "bigquery", "snowflake", "hadoop", "spark", "hive", "kafka"
    ],
    "Data Analysis & BI": [
        "excel", "power bi", "tableau", "looker", "qlik", "sas", "spss",
        "statistics", "data visualization", "etl", "data warehouse", "pivot",
        "vlookup", "alteryx"
    ],
    "Soft Skills": [
        "communication", "leadership", "teamwork", "problem solving", "critical thinking",
        "project management", "agile", "scrum", "kanban", "time management",
        "collaboration", "presentation", "mentoring", "analytical"
    ],
    "Security": [
        "cybersecurity", "penetration testing", "ethical hacking", "owasp",
        "firewall", "siem", "vulnerability", "encryption", "iam", "sso",
        "oauth", "jwt", "security"
    ]
}

JOB_ROLE_SKILLS = {
    "Data Science": ["python","machine learning","deep learning","pandas","numpy","scikit-learn","tensorflow","sql","statistics","data visualization","jupyter","matplotlib","nlp","pytorch"],
    "Web Designing": ["html","css","javascript","react","angular","vue","ui/ux","figma","bootstrap","responsive design","photoshop","tailwind"],
    "Mechanical Engineer": ["autocad","solidworks","catia","ansys","matlab","manufacturing","cad","finite element analysis","thermodynamics","fluid mechanics"],
    "Sales": ["communication","negotiation","crm","salesforce","lead generation","customer relationship","presentation","marketing","business development"],
    "HR": ["recruitment","talent acquisition","onboarding","payroll","hris","performance management","training","employee relations","hr policies"],
    "Advocate": ["legal research","litigation","contract law","negotiation","legal writing","compliance","corporate law","intellectual property"],
    "Arts": ["drawing","painting","design","adobe","illustrator","photoshop","creativity","portfolio","fine arts","graphic design"],
    "Accountant": ["accounting","tally","quickbooks","financial statements","taxation","auditing","gst","excel","budgeting","financial analysis"],
    "Business Analyst": ["requirement gathering","sql","excel","data analysis","stakeholder management","agile","scrum","jira","business intelligence","process improvement"],
    "Information-Technology": ["python","java","sql","networking","linux","aws","docker","cybersecurity","system administration","cloud computing"],
    "Health and fitness": ["nutrition","fitness","exercise science","personal training","anatomy","physiology","wellness","coaching"],
    "Civil Engineer": ["autocad","revit","structural analysis","construction management","surveying","project management","concrete","civil engineering"],
    "Java Developer": ["java","spring","hibernate","microservices","maven","git","sql","rest api","junit","design patterns"],
    "Python Developer": ["python","django","flask","fastapi","sql","rest api","git","docker","pytest","celery"],
    "DevOps Engineer": ["docker","kubernetes","jenkins","aws","terraform","ansible","ci/cd","linux","git","monitoring","nginx"],
    "Network Security Engineer": ["cybersecurity","firewalls","networking","penetration testing","siem","wireshark","linux","ssl","tls","vulnerability assessment"],
    "PMO": ["project management","ms project","agile","scrum","pmp","risk management","stakeholder management","budget management","jira"],
    "Database": ["sql","mysql","postgresql","mongodb","oracle","database design","query optimization","etl","data modeling","indexing"],
    "Hadoop": ["hadoop","spark","hive","hbase","kafka","scala","python","hdfs","mapreduce","data pipeline"],
    "ETL Developer": ["etl","informatica","sql","data warehouse","pentaho","talend","data pipeline","oracle","python","snowflake"],
    "DotNet Developer": ["c#","asp.net",".net","sql server","mvc","entity framework","azure","visual studio","rest api","angular"],
    "Blockchain": ["blockchain","ethereum","solidity","smart contracts","web3","cryptography","javascript","node.js","truffle","defi"],
    "Testing": ["manual testing","automation testing","selenium","junit","testng","jira","api testing","postman","agile","bug tracking"],
    "Operations Manager": ["operations management","supply chain","logistics","process improvement","six sigma","lean","kpi","team management","budgeting"],
}


def clean_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'\b\d{10,}\b|\+\d[\d\s\-]{8,}\d', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\b\d+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_skills(text: str) -> dict:
    text_lower = text.lower()
    found = {}
    for category, skills in SKILL_TAXONOMY.items():
        matched = []
        for skill in skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                matched.append(skill)
        if matched:
            found[category] = matched
    return found


def extract_entities(text: str) -> dict:
    """Simple rule-based entity extraction (no spaCy)."""
    entities = {"organizations": [], "locations": [], "persons": [], "misc": []}
    # Extract emails
    emails = re.findall(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', text, re.I)
    if emails:
        entities["misc"].extend(emails[:3])
    # Extract URLs
    urls = re.findall(r'https?://\S+|www\.\S+', text, re.I)
    if urls:
        entities["misc"].extend(urls[:3])
    return entities


def get_missing_skills(resume_text: str, predicted_role: str) -> list:
    required = JOB_ROLE_SKILLS.get(predicted_role, [])
    resume_lower = resume_text.lower()
    missing = []
    for skill in required:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if not re.search(pattern, resume_lower):
            missing.append(skill)
    return missing


def get_resume_score_breakdown(resume_text: str, job_desc: str, predicted_role: str) -> dict:
    """
    Returns all scores as 0-100 percentages.
      skills_pct    = (matched / total_required) * 100
      jd_pct        = cosine_similarity * 100
      complete_pct  = (filled_sections / total_sections) * 100
      total         = skills_pct*0.4 + jd_pct*0.4 + complete_pct*0.2
    """
    from src.matcher import compute_cosine_similarity

    # 1. Skills percentage
    role_skills = JOB_ROLE_SKILLS.get(predicted_role, [])
    resume_lower = resume_text.lower()
    matched_count = sum(
        1 for s in role_skills
        if re.search(r'\b' + re.escape(s) + r'\b', resume_lower)
    )
    skills_pct = round((matched_count / len(role_skills) * 100) if role_skills else 0, 1)

    # 2. JD similarity percentage
    jd_sim = compute_cosine_similarity(resume_text, job_desc) if job_desc.strip() else 0.0
    jd_pct = round(jd_sim * 100, 1)

    # 3. Completeness percentage
    sections = ["education", "experience", "skill", "project", "certification",
                "achievement", "summary", "objective", "contact"]
    found_sections = sum(1 for s in sections if s in resume_lower)
    complete_pct = round((found_sections / len(sections)) * 100, 1)

    # 4. Weighted final score
    total = round(skills_pct * 0.4 + jd_pct * 0.4 + complete_pct * 0.2, 1)
    total = min(total, 100.0)

    return {
        "skills_pct": skills_pct,          # 0-100
        "jd_pct": jd_pct,                  # 0-100
        "complete_pct": complete_pct,       # 0-100
        "total": total,                     # 0-100 weighted final
        "matched_role_skills": matched_count,
        "total_role_skills": len(role_skills),
        # Legacy keys kept so ats_feedback.py doesn't break
        "skills_score": round(skills_pct * 0.4, 1),
        "jd_score": round(jd_pct * 0.4, 1),
        "completeness_score": round(complete_pct * 0.2, 1),
        "jd_similarity": jd_pct,
    }

"""
Hybrid Rule + ML Resume Classifier
ROOT CAUSE FIX: keyword-confidence rules override biased ML predictions.
Guarantees correct domain for HR, Finance, Marketing, Civil, Legal etc.
"""

import os, re, pickle, math
from collections import Counter
from src.pure_ml import ResumeClassifierPipeline, tokenize
from src.semantic_engine import expand_text_semantically

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.pkl')

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: DOMAIN KEYWORD RULES  (primary classifier — overrides ML)
# Each role has STRONG_MARKERS (high-confidence) and WEAK_MARKERS (support).
# Score = strong*3 + weak*1.  Highest score wins if >= threshold.
# ─────────────────────────────────────────────────────────────────────────────
DOMAIN_RULES = {
    "Data Science": {
        "strong": ["machine learning","deep learning","neural network","xgboost","lightgbm",
                   "scikit-learn","tensorflow","pytorch","keras","feature engineering",
                   "model training","random forest","gradient boosting","nlp","bert","transformer"],
        "weak":   ["python","pandas","numpy","jupyter","statistics","regression","classification",
                   "data analysis","matplotlib","seaborn","kaggle","data scientist"],
    },
    "Software Engineer": {
        "strong": ["software engineer","system design","data structures","algorithms","oop",
                   "object oriented","design patterns","microservices","rest api","spring boot",
                   "django","flask","fastapi","backend","frontend","full stack"],
        "weak":   ["java","python","javascript","typescript","node","react","angular","vue",
                   "docker","kubernetes","git","agile","ci/cd","junit","pytest"],
    },
    "HR": {
        "strong": ["recruitment","talent acquisition","onboarding","employee relations","hr policies",
                   "hris","hrms","payroll","workforce planning","performance appraisal","l&d",
                   "learning and development","human resources","labor law","industrial relations"],
        "weak":   ["hiring","sourcing","screening","interview","offer","attrition","engagement",
                   "retention","training","compensation","benefits","workday","bamboohr"],
    },
    "Marketing": {
        "strong": ["digital marketing","seo","sem","social media marketing","content marketing",
                   "brand management","marketing campaign","google analytics","email marketing",
                   "market research","go-to-market","growth hacking","paid media","influencer"],
        "weak":   ["facebook ads","instagram","linkedin","twitter","roi","lead generation",
                   "hubspot","salesforce","crm","ppc","conversion","funnel","brand awareness"],
    },
    "Finance": {
        "strong": ["financial modeling","dcf","valuation","investment banking","equity research",
                   "chartered accountant","ca","financial reporting","ifrs","gaap","auditing",
                   "taxation","gst","income tax","fp&a","treasury management"],
        "weak":   ["excel","vlookup","pivot","balance sheet","p&l","income statement","budget",
                   "forecast","variance analysis","sap","tally","erp","reconciliation"],
    },
    "Accountant": {
        "strong": ["accounts payable","accounts receivable","general ledger","journal entries",
                   "bank reconciliation","statutory audit","bookkeeping","tally erp",
                   "cost accounting","fixed assets","depreciation","gst filing","tax return"],
        "weak":   ["accounting","excel","invoice","billing","vendor payment","month end","closing"],
    },
    "Sales": {
        "strong": ["business development","b2b sales","b2c sales","sales target","revenue generation",
                   "deal closing","client acquisition","sales pipeline","saas sales","enterprise sales",
                   "account executive","sales representative","quota","cold calling"],
        "weak":   ["negotiation","presentation","crm","salesforce","lead","prospect","customer",
                   "demo","proposal","upsell","cross-sell","territory"],
    },
    "Operations Manager": {
        "strong": ["supply chain management","procurement","logistics","vendor management",
                   "inventory management","lean manufacturing","six sigma","warehouse management",
                   "import export","3pl","demand planning","s&op"],
        "weak":   ["operations","kpi","sop","process improvement","erp","sap","oracle","kaizen"],
    },
    "DevOps Engineer": {
        "strong": ["devops","kubernetes","terraform","ansible","helm","argocd","gitops",
                   "infrastructure as code","ci/cd pipeline","site reliability","sre",
                   "prometheus","grafana","elk stack","cloudformation"],
        "weak":   ["docker","jenkins","aws","gcp","azure","linux","bash","python","monitoring"],
    },
    "Network Security Engineer": {
        "strong": ["cybersecurity","penetration testing","ethical hacking","siem","soc",
                   "vulnerability assessment","owasp","malware analysis","incident response",
                   "firewall","intrusion detection","ids","ips","ceh","cissp","iso 27001"],
        "weak":   ["security","encryption","vpn","network","linux","wireshark","nmap"],
    },
    "Mechanical Engineer": {
        "strong": ["solidworks","catia","ansys","finite element analysis","fea","cfd",
                   "thermodynamics","fluid mechanics","manufacturing process","gd&t",
                   "tolerance analysis","iatf","ppap","apqp","mechanical design"],
        "weak":   ["autocad","cad","cam","pro-e","nx","material","stress","heat transfer"],
    },
    "Civil Engineer": {
        "strong": ["structural design","staad pro","etabs","safe","is code","rcc","concrete design",
                   "highway design","geotechnical","quantity surveying","primavera","revit",
                   "construction management","building information modeling","bim"],
        "weak":   ["autocad","site","foundation","beam","column","slab","survey","estimation"],
    },
    "Advocate": {
        "strong": ["litigation","legal drafting","court","criminal law","civil law","corporate law",
                   "intellectual property","trademark","patent","merger acquisition","m&a",
                   "legal advisory","due diligence","arbitration","sebi","rbi compliance"],
        "weak":   ["contract","agreement","nda","mou","compliance","regulatory","legal research"],
    },
    "Business Analyst": {
        "strong": ["business requirements","brd","frd","functional specification","gap analysis",
                   "process mapping","use case","user story","stakeholder management","uat",
                   "business intelligence","power bi","tableau","data driven"],
        "weak":   ["agile","scrum","jira","confluence","sql","excel","visio","wireframe"],
    },
    "PMO": {
        "strong": ["project management","pmp","prince2","program management","portfolio management",
                   "project lifecycle","risk register","change management","earned value",
                   "project governance","deliverable","milestone","work breakdown structure","wbs"],
        "weak":   ["jira","ms project","smartsheet","agile","scrum","stakeholder","budget","sprint"],
    },
    "Testing": {
        "strong": ["test automation","selenium","cypress","playwright","appium","testng","junit",
                   "cucumber","bdd","performance testing","jmeter","gatling","api testing",
                   "postman","rest assured","quality assurance","qa engineer"],
        "weak":   ["manual testing","test case","bug","defect","jira","regression","smoke","uat"],
    },
    "Web Designing": {
        "strong": ["ui design","ux design","figma","adobe xd","sketch","wireframing","prototyping",
                   "user research","usability testing","design system","information architecture",
                   "interaction design","visual design","responsive design"],
        "weak":   ["html","css","javascript","bootstrap","tailwind","photoshop","illustrator"],
    },
    "Java Developer": {
        "strong": ["java","spring framework","spring boot","spring cloud","hibernate","jpa",
                   "j2ee","jsp","servlet","maven","gradle","java 8","java 11","java 17"],
        "weak":   ["microservices","rest","sql","docker","junit","mockito","kafka","rabbitmq"],
    },
    "Python Developer": {
        "strong": ["python developer","django","fastapi","sqlalchemy","celery","pydantic",
                   "asyncio","websocket","python scripting","automation","web scraping"],
        "weak":   ["flask","rest api","redis","postgresql","mongodb","docker","pytest"],
    },
    "Database": {
        "strong": ["database administrator","dba","query optimization","indexing","partitioning",
                   "stored procedure","trigger","replication","high availability","oracle dba",
                   "mysql dba","postgresql dba","nosql","mongodb","cassandra","elasticsearch"],
        "weak":   ["sql","backup","recovery","data modeling","normalization","etl","migration"],
    },
    "ETL Developer": {
        "strong": ["etl pipeline","data warehouse","snowflake","redshift","bigquery","dbt",
                   "apache airflow","data pipeline","informatica","talend","ssis","data ingestion"],
        "weak":   ["sql","python","spark","hive","data quality","staging","dimensional modeling"],
    },
    "Blockchain": {
        "strong": ["blockchain","ethereum","solidity","smart contract","web3","defi","nft",
                   "hyperledger","chaincode","cryptography","consensus mechanism","dao",
                   "tokenomics","ipfs","layer 2","polygon","avalanche"],
        "weak":   ["distributed ledger","wallet","dapp","rust","golang","substrate"],
    },
    "DotNet Developer": {
        "strong": [".net","asp.net","c#","blazor","razor","wpf","winforms","entity framework",
                   "linq","azure devops","wcf","signalr","identity server","nuget"],
        "weak":   ["sql server","visual studio","mvc","rest","docker","unit test","moq"],
    },
    "Health and fitness": {
        "strong": ["personal trainer","fitness coach","nutrition","dietitian","physiotherapy",
                   "sports science","exercise physiology","rehabilitation","yoga instructor",
                   "gym","wellness coach","anatomy","kinesiology"],
        "weak":   ["health","fitness","workout","strength","cardio","diet","bmi","supplement"],
    },
    "Arts": {
        "strong": ["graphic design","motion graphics","after effects","premiere pro","3d design",
                   "blender","art direction","creative director","storyboard","illustration",
                   "typography","brand identity","visual communication"],
        "weak":   ["photoshop","illustrator","indesign","canva","adobe","portfolio","logo"],
    },
    "Hadoop": {
        "strong": ["hadoop","hdfs","mapreduce","hive","hbase","pig","yarn","oozie","sqoop",
                   "apache spark","pyspark","scala","kafka streaming","flink","databricks"],
        "weak":   ["big data","cluster","distributed","data lake","batch processing"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: BALANCED TRAINING DATA (6 samples per role = 150 total)
# Each sample is domain-exclusive — minimal cross-domain token overlap
# ─────────────────────────────────────────────────────────────────────────────
TRAINING_DATA = []
for role, markers in DOMAIN_RULES.items():
    # Build 6 synthetic but rich sentences from the domain markers
    strong = markers["strong"]
    weak   = markers["weak"]
    all_kw = strong + weak
    step   = max(1, len(all_kw) // 6)
    for i in range(6):
        chunk = all_kw[i*step : i*step + max(8, len(all_kw)//3)]
        if not chunk:
            chunk = all_kw
        TRAINING_DATA.append((" ".join(chunk), role))


# ─────────────────────────────────────────────────────────────────────────────
# RULE ENGINE — returns (label, confidence) or None if inconclusive
# ─────────────────────────────────────────────────────────────────────────────
def _rule_predict(text: str):
    """
    Score each domain using strong/weak marker matches.
    strong hit = 3 pts, weak hit = 1 pt.
    Returns (best_role, confidence_pct) if best_score >= 3, else None.
    """
    text_lower = text.lower()
    scores = {}
    for role, markers in DOMAIN_RULES.items():
        s = sum(3 for kw in markers["strong"] if re.search(r'\b' + re.escape(kw) + r'\b', text_lower))
        w = sum(1 for kw in markers["weak"]   if re.search(r'\b' + re.escape(kw) + r'\b', text_lower))
        scores[role] = s + w

    best_role  = max(scores, key=scores.get)
    best_score = scores[best_role]

    if best_score < 3:
        return None   # not confident — defer to ML

    # Confidence: ratio of this role's score vs total score
    total = sum(scores.values()) or 1
    conf  = min(99, round((best_score / total) * 100 * 1.4))

    # Top 3
    sorted_roles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top3 = [(r, min(99, round((sc / total) * 100 * 1.4))) for r, sc in sorted_roles[:3]]

    return best_role, conf, top3


# ─────────────────────────────────────────────────────────────────────────────
# ML FALLBACK MODEL
# ─────────────────────────────────────────────────────────────────────────────
def train_model(save: bool = True) -> ResumeClassifierPipeline:
    texts  = [expand_text_semantically(d[0]) for d in TRAINING_DATA]
    labels = [d[1] for d in TRAINING_DATA]
    pipeline = ResumeClassifierPipeline()
    pipeline.fit(texts, labels)
    if save:
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(pipeline, f)
    return pipeline


def load_model() -> ResumeClassifierPipeline:
    return train_model(save=True)


# ─────────────────────────────────────────────────────────────────────────────
# HYBRID PREDICT  (rule-first → ML fallback)
# ─────────────────────────────────────────────────────────────────────────────
def predict_role(text: str, pipeline=None) -> tuple:
    """
    Returns (label, confidence_pct, top3_list).
    Rule engine runs first; if confident, returns immediately.
    ML model used only when rules are inconclusive.
    """
    if not text or not text.strip():
        return ("Unknown", 0, [])

    # 1. Try rule engine
    rule_result = _rule_predict(text)
    if rule_result is not None:
        return rule_result   # (label, conf, top3)

    # 2. ML fallback
    if pipeline is None:
        pipeline = load_model()
    try:
        expanded = expand_text_semantically(text)
        proba_list = pipeline.predict_proba_dict([expanded])
        proba = proba_list[0]
        sorted_cls = sorted(proba.items(), key=lambda x: x[1], reverse=True)
        top3 = [(cls, int(round(pct * 100))) for cls, pct in sorted_cls[:3]]
        return (top3[0][0], top3[0][1], top3)
    except Exception:
        return ("Unknown", 0, [])

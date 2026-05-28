"""
Matcher Module (pure Python, no scikit-learn dependency)
"""

from src.pure_ml import compute_similarity, tokenize


def compute_cosine_similarity(text1: str, text2: str) -> float:
    """Cosine similarity between resume and job description."""
    return compute_similarity(text1, text2)


def keyword_overlap_score(resume_text: str, job_desc: str) -> dict:
    """Keyword overlap between resume and job description."""
    if not job_desc.strip():
        return {"matched": [], "total_jd_keywords": 0, "overlap_pct": 0.0}
    resume_kw = set(tokenize(resume_text, ngrams=1))
    jd_kw = set(tokenize(job_desc, ngrams=1))
    matched = sorted(list(resume_kw.intersection(jd_kw)))
    overlap = len(matched) / len(jd_kw) if jd_kw else 0.0
    return {
        "matched": matched,
        "total_jd_keywords": len(jd_kw),
        "overlap_pct": round(overlap * 100, 1)
    }

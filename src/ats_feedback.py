"""
ATS Feedback Module
Generates ATS-style feedback, suggestions, and improvement tips.
"""

from src.text_processor import JOB_ROLE_SKILLS, SKILL_TAXONOMY


# ─────────────────────────────────────────────────────────────────────────────
# ATS SECTION KEYWORDS
# ─────────────────────────────────────────────────────────────────────────────
RESUME_SECTIONS = {
    "Contact Info": ["phone", "email", "linkedin", "github", "address", "contact"],
    "Summary/Objective": ["summary", "objective", "about me", "profile", "overview", "career objective"],
    "Education": ["education", "university", "college", "degree", "bachelor", "master", "phd", "b.tech", "m.tech", "b.sc", "m.sc"],
    "Work Experience": ["experience", "work experience", "employment", "job history", "internship", "career"],
    "Skills": ["skill", "technical skills", "core competencies", "expertise", "tools", "technologies"],
    "Projects": ["project", "portfolio", "work sample", "case study", "implementation"],
    "Certifications": ["certification", "certificate", "certified", "coursera", "udemy", "aws certified", "google certified"],
    "Achievements": ["achievement", "award", "recognition", "honor", "accomplishment", "accolade"],
}

ATS_ACTION_VERBS = [
    "achieved", "built", "created", "designed", "developed", "enhanced",
    "implemented", "improved", "led", "managed", "optimized", "reduced",
    "streamlined", "trained", "transformed", "delivered", "launched"
]

QUANTIFICATION_PATTERNS = [
    r'\d+%', r'\$[\d,]+', r'\d+ (users|clients|projects|teams|members|employees)',
    r'increased.*by.*\d', r'reduced.*by.*\d', r'improved.*by.*\d'
]


def check_resume_sections(text: str) -> dict:
    """
    Check which standard resume sections are present.
    Returns dict: {section: True/False}
    """
    text_lower = text.lower()
    results = {}
    for section, keywords in RESUME_SECTIONS.items():
        results[section] = any(kw in text_lower for kw in keywords)
    return results


def check_action_verbs(text: str) -> dict:
    """Check presence of strong action verbs."""
    text_lower = text.lower()
    found = [v for v in ATS_ACTION_VERBS if v in text_lower]
    return {
        "found": found,
        "count": len(found),
        "has_enough": len(found) >= 5
    }


def check_quantification(text: str) -> dict:
    """Check if achievements are quantified with numbers/percentages."""
    import re
    found = []
    for pattern in QUANTIFICATION_PATTERNS:
        matches = re.findall(pattern, text.lower())
        found.extend(matches)
    return {
        "found": found[:10],  # top 10
        "has_quantification": len(found) > 0
    }


def estimate_word_count(text: str) -> dict:
    """Estimate word count and recommend range."""
    words = text.split()
    count = len(words)
    if count < 200:
        status = "Too Short"
        tip = "Add more content — describe projects, experience, and skills in detail."
    elif count <= 700:
        status = "Good Length"
        tip = "Resume length is optimal for ATS parsing."
    elif count <= 1200:
        status = "Slightly Long"
        tip = "Consider trimming to 1 page for junior roles."
    else:
        status = "Too Long"
        tip = "Shorten to 1-2 pages. ATS may truncate very long resumes."
    return {"word_count": count, "status": status, "tip": tip}


def generate_ats_feedback(
    resume_text: str,
    predicted_role: str,
    missing_skills: list,
    score: dict
) -> dict:
    """
    Generate comprehensive ATS feedback.
    Returns structured feedback dict. ALWAYS contains >=3 recommendations.
    """
    feedback = {}

    # Section analysis
    sections = check_resume_sections(resume_text)
    missing_sections = [s for s, present in sections.items() if not present]
    feedback["sections"] = sections
    feedback["missing_sections"] = missing_sections

    # Action verbs
    verbs = check_action_verbs(resume_text)
    feedback["action_verbs"] = verbs

    # Quantification
    quant = check_quantification(resume_text)
    feedback["quantification"] = quant

    # Word count
    wc = estimate_word_count(resume_text)
    feedback["word_count"] = wc

    # Overall rating
    total = score.get("total", 0)
    if total >= 80:
        rating = "Excellent ✅"
        summary = "Your resume is well-optimized for ATS systems. Great job!"
    elif total >= 60:
        rating = "Good 👍"
        summary = "Your resume passes basic ATS checks. A few improvements can make it stronger."
    elif total >= 40:
        rating = "Fair ⚠️"
        summary = "Your resume needs improvement. Focus on the suggestions below."
    else:
        rating = "Needs Work ❌"
        summary = "Significant improvements needed. Follow the recommendations below."
    feedback["rating"] = rating
    feedback["summary"] = summary

    # ── RECOMMENDATIONS (GUARANTEED >=3) ─────────────────────────────────────
    recommendations = []

    # 1. Missing skills
    if missing_skills:
        top_missing = missing_skills[:5]
        recommendations.append(
            f"🔧 **Add Missing Skills**: Include these key skills for {predicted_role}: "
            f"{', '.join(top_missing)}. Add them explicitly in your Skills section."
        )

    # 2. Missing sections
    if missing_sections:
        recommendations.append(
            f"📋 **Add Missing Sections**: Your resume is missing: {', '.join(missing_sections[:4])}. "
            f"ATS systems parse structured sections to extract relevant data."
        )

    # 3. Action verbs
    if not verbs["has_enough"]:
        recommendations.append(
            "💪 **Use Strong Action Verbs**: Start every bullet point with a power verb: "
            "'Developed', 'Built', 'Led', 'Optimized', 'Delivered', 'Achieved'. "
            f"You currently have {verbs['count']} — aim for 8+."
        )
    else:
        recommendations.append(
            f"✅ **Action Verbs**: Good! You have {verbs['count']} strong verbs. "
            "Keep each bullet starting with an action verb for maximum ATS impact."
        )

    # 4. Quantification (always shown — positive or negative)
    if not quant["has_quantification"]:
        recommendations.append(
            "📊 **Quantify Your Impact**: Add concrete numbers, metrics, and results. "
            "Example: 'Increased performance by 35%', 'Managed team of 10', 'Reduced costs by $50K'. "
            "Quantified achievements score significantly higher in ATS."
        )
    else:
        recommendations.append(
            "✅ **Quantified Achievements Found**: Great — keep adding more metrics. "
            "Try to quantify at least one achievement per role or project."
        )

    # 5. Word count
    if wc["status"] in ("Too Short", "Too Long"):
        recommendations.append(f"📝 **Resume Length**: {wc['tip']}")
    else:
        recommendations.append(
            f"✅ **Resume Length**: {wc['word_count']} words — optimal length for ATS parsing. "
            "Maintain this range (300-700 words) for best results."
        )

    # 6. JD match tip (always shown)
    jd_sim = score.get("jd_similarity", 0)
    if jd_sim == 0:
        recommendations.append(
            "🎯 **Paste a Job Description**: Add the target JD in the sidebar to unlock "
            "keyword match analysis, JD similarity score, and role-specific improvement tips."
        )
    elif jd_sim < 40:
        recommendations.append(
            f"🎯 **Low JD Match ({jd_sim:.0f}%)**: Tailor your resume to the job posting. "
            "Mirror exact keywords, job title, tools and requirements from the JD. "
            "ATS filters resumes by keyword density before a human ever reads them."
        )
    elif jd_sim < 70:
        recommendations.append(
            f"🎯 **Improve JD Match ({jd_sim:.0f}%)**: Add more JD-specific terms. "
            "Look for skills or tools mentioned in the JD that are missing from your resume."
        )
    else:
        recommendations.append(
            f"✅ **Strong JD Match ({jd_sim:.0f}%)**: Your resume aligns well with the job description. "
            "Ensure the exact job title from the JD appears in your resume summary."
        )

    # 7. Universal ATS best-practice tip (always appended)
    recommendations.append(
        "💡 **ATS Best Practices**: Use standard section headings (Skills, Experience, Education). "
        "Avoid tables, images, headers/footers and multi-column layouts — ATS parsers "
        "cannot read them reliably. Save and submit as PDF."
    )

    feedback["recommendations"] = recommendations

    # Skill improvement tips by category
    skill_tips = []
    if missing_skills:
        skill_tips.append(
            f"For a **{predicted_role}** role, prioritize learning: "
            + ", ".join(missing_skills[:5])
        )
        skill_tips.append(
            "Add these as individual bullet points under a **Technical Skills** section."
        )
        skill_tips.append(
            "Consider online courses (Coursera, Udemy, LinkedIn Learning) and add certifications to your resume."
        )
    else:
        skill_tips.append(
            f"Your skills align well with the **{predicted_role}** role requirements."
        )
        skill_tips.append(
            "Keep skills section updated as you learn new tools and technologies."
        )
    feedback["skill_tips"] = skill_tips

    return feedback

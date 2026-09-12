"""
ATS Resume Checker
Developer Job Application Tracker PRO - Bonus Script
CreatorDockStudio

Analyzes your resume against a job description and gives:
- ATS compatibility score (0-100)
- Missing keywords
- Keyword density analysis
- Formatting issues
- Improvement recommendations

Usage:
    python ats_resume_checker.py

Requirements:
    pip install python-docx PyPDF2
"""

import re
import os
from collections import Counter

# ─── Try optional imports ───────────────────────────────────────────────────
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# ─── Keyword Banks ──────────────────────────────────────────────────────────

TECH_SKILLS = {
    "languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
        "kotlin", "swift", "ruby", "php", "scala", "r", "dart", "bash", "sql"
    ],
    "frontend": [
        "react", "vue", "angular", "next.js", "nuxt", "svelte", "html", "css",
        "sass", "tailwind", "webpack", "vite", "redux", "graphql", "rest api"
    ],
    "backend": [
        "node.js", "express", "django", "flask", "fastapi", "spring", "rails",
        "laravel", "microservices", "rest", "grpc", "rabbitmq", "kafka"
    ],
    "database": [
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb",
        "cassandra", "sqlite", "oracle", "sql server", "firebase"
    ],
    "cloud_devops": [
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible",
        "ci/cd", "jenkins", "github actions", "linux", "nginx", "prometheus"
    ],
    "practices": [
        "agile", "scrum", "tdd", "bdd", "clean code", "solid", "design patterns",
        "code review", "pair programming", "microservices", "api design"
    ],
    "soft_skills": [
        "communication", "collaboration", "problem solving", "leadership",
        "mentoring", "teamwork", "ownership", "initiative", "analytical"
    ]
}

ATS_UNFRIENDLY_PATTERNS = [
    (r'\t', "Tabs found — use spaces instead"),
    (r'[│┃|]{2,}', "Table-like characters detected — ATS can't parse tables"),
    (r'•|◦|▪|▸|►|✓|✔|★|☆', "Special bullet characters — use simple hyphens (-)"),
    (r'@[A-Za-z0-9_]+\s*\n', "Social handle without context — spell out LinkedIn URL"),
]

POWER_VERBS = [
    "achieved", "built", "created", "delivered", "designed", "developed",
    "drove", "engineered", "established", "implemented", "improved", "increased",
    "launched", "led", "managed", "optimized", "reduced", "scaled", "shipped",
    "solved", "spearheaded", "streamlined", "transformed"
]

WEAK_VERBS = [
    "worked on", "helped with", "assisted", "was responsible for",
    "participated in", "involved in", "tried to", "attempted"
]


# ─── Text Extraction ─────────────────────────────────────────────────────────

def extract_text_from_docx(path: str) -> str:
    if not DOCX_AVAILABLE:
        raise ImportError("Install python-docx:  pip install python-docx")
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text_from_pdf(path: str) -> str:
    if not PDF_AVAILABLE:
        raise ImportError("Install PyPDF2:  pip install PyPDF2")
    text = []
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)


def extract_text_from_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def load_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return extract_text_from_docx(path)
    elif ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext in (".txt", ".md"):
        return extract_text_from_txt(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}  (use .docx / .pdf / .txt)")


# ─── Analysis Functions ──────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    """Lowercase word tokens, keeping multi-word phrases via bigrams."""
    words = re.findall(r"[a-z0-9#+./'-]+", text.lower())
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
    return words + bigrams


def keyword_match(resume_tokens: list[str], jd_tokens: list[str]) -> dict:
    jd_freq = Counter(jd_tokens)
    resume_set = set(resume_tokens)

    matched, missing = [], []
    for kw, freq in jd_freq.most_common():
        if len(kw) < 3:
            continue
        if kw in resume_set:
            matched.append((kw, freq))
        else:
            missing.append((kw, freq))

    return {"matched": matched[:30], "missing": missing[:30]}


def tech_skill_analysis(resume_tokens: list[str]) -> dict:
    found, absent = {}, {}
    for category, skills in TECH_SKILLS.items():
        f = [s for s in skills if s in resume_tokens]
        a = [s for s in skills if s not in resume_tokens]
        if f:
            found[category] = f
        if a:
            absent[category] = a
    return {"found": found, "absent": absent}


def ats_formatting_check(resume_text: str) -> list[str]:
    issues = []
    for pattern, message in ATS_UNFRIENDLY_PATTERNS:
        if re.search(pattern, resume_text):
            issues.append(message)
    if len(resume_text) < 400:
        issues.append("Resume seems very short — aim for 400-800 words")
    if len(resume_text) > 6000:
        issues.append("Resume may be too long — keep it to 1-2 pages (~800 words)")
    return issues


def action_verb_check(resume_text: str) -> dict:
    text_lower = resume_text.lower()
    used_power = [v for v in POWER_VERBS if v in text_lower]
    used_weak = [v for v in WEAK_VERBS if v in text_lower]
    return {"power_verbs_used": used_power, "weak_phrases_found": used_weak}


def quantification_check(resume_text: str) -> dict:
    numbers = re.findall(r'\b\d+[%xkm+]?\b', resume_text, re.IGNORECASE)
    has_percentages = bool(re.search(r'\d+\s*%', resume_text))
    has_dollar = bool(re.search(r'\$[\d,]+', resume_text))
    return {
        "numbers_found": len(numbers),
        "has_percentages": has_percentages,
        "has_dollar_amounts": has_dollar,
        "recommendation": "Add metrics: 'Reduced load time by 40%', 'Managed team of 5'" if len(numbers) < 3 else "Good — resume has quantifiable achievements"
    }


def calculate_ats_score(
    matched_ratio: float,
    formatting_issues: list,
    weak_phrases: list,
    quant: dict
) -> tuple[int, str]:
    score = 100

    # Keyword match (−40 max)
    score -= int((1 - min(matched_ratio, 1)) * 40)

    # Formatting (−5 per issue, max −20)
    score -= min(len(formatting_issues) * 5, 20)

    # Weak phrases (−3 each, max −15)
    score -= min(len(weak_phrases) * 3, 15)

    # Quantification (−10 if none)
    if quant["numbers_found"] < 2:
        score -= 10

    score = max(0, min(100, score))

    if score >= 80:
        grade = "EXCELLENT — Very likely to pass ATS"
    elif score >= 65:
        grade = "GOOD — Should pass most ATS systems"
    elif score >= 50:
        grade = "FAIR — Some ATS systems may filter this out"
    else:
        grade = "POOR — High risk of ATS rejection"

    return score, grade


# ─── Report ──────────────────────────────────────────────────────────────────

def print_section(title: str, char: str = "-", width: int = 70):
    print(f"\n{'-' * width}")
    print(f"  {title}")
    print(f"{'-' * width}")


def generate_report(resume_path: str, jd_path: str | None = None):
    print("\n" + "=" * 70)
    print("  ATS RESUME CHECKER - CreatorDockStudio")
    print("=" * 70)

    # Load resume
    print(f"\n[RESUME] Loading: {resume_path}")
    resume_text = load_text(resume_path)
    resume_tokens = tokenize(resume_text)

    # Load job description (optional)
    jd_tokens = []
    if jd_path and os.path.exists(jd_path):
        print(f"[JD] Loading: {jd_path}")
        jd_text = load_text(jd_path)
        jd_tokens = tokenize(jd_text)

    # ── Formatting Check ──
    print_section("1. ATS FORMATTING CHECK")
    issues = ats_formatting_check(resume_text)
    if issues:
        for issue in issues:
            print(f"  ⚠  {issue}")
    else:
        print("  ✓  No formatting issues detected")

    # ── Keyword Match ──
    if jd_tokens:
        print_section("2. KEYWORD MATCH (vs Job Description)")
        km = keyword_match(resume_tokens, jd_tokens)
        matched = km["matched"]
        missing = km["missing"]

        matched_ratio = len(matched) / max(len(matched) + len(missing), 1)
        print(f"\n  Match rate: {matched_ratio*100:.0f}%  ({len(matched)} matched / {len(matched)+len(missing)} total JD keywords)\n")

        if matched:
            print(f"  ✅ Keywords FOUND in resume ({len(matched)}):")
            for kw, freq in matched[:15]:
                print(f"      • {kw}")

        if missing:
            print(f"\n  ❌ HIGH-PRIORITY missing keywords ({len(missing)}):")
            for kw, freq in missing[:15]:
                print(f"      • {kw}  (appears {freq}x in JD)")
    else:
        matched_ratio = 0.5  # neutral if no JD provided

    # ── Tech Skills ──
    print_section("3. TECH SKILL COVERAGE")
    skill_data = tech_skill_analysis(resume_tokens)
    for category, skills in skill_data["found"].items():
        print(f"  ✓  {category.upper()}: {', '.join(skills)}")
    print()
    for category, skills in list(skill_data["absent"].items())[:3]:
        print(f"  ⚠  Not detected — {category.upper()}: {', '.join(skills[:6])}")

    # ── Action Verbs ──
    print_section("4. ACTION VERBS & LANGUAGE")
    verb_data = action_verb_check(resume_text)
    if verb_data["power_verbs_used"]:
        print(f"  ✓  Power verbs found: {', '.join(verb_data['power_verbs_used'][:8])}")
    else:
        print("  ⚠  No strong action verbs detected — add verbs like 'built', 'shipped', 'optimized'")

    if verb_data["weak_phrases_found"]:
        print(f"\n  ❌ Weak phrases to REMOVE:")
        for phrase in verb_data["weak_phrases_found"]:
            print(f"      • '{phrase}'  → replace with active verb")

    # ── Quantification ──
    print_section("5. QUANTIFICATION CHECK")
    quant = quantification_check(resume_text)
    print(f"  Numbers/metrics found: {quant['numbers_found']}")
    print(f"  Percentages: {'Yes ✓' if quant['has_percentages'] else 'No ⚠'}")
    print(f"  Dollar amounts: {'Yes ✓' if quant['has_dollar_amounts'] else 'No'}")
    print(f"\n  → {quant['recommendation']}")

    # ── ATS Score ──
    print_section("6. OVERALL ATS SCORE")
    score, grade = calculate_ats_score(
        matched_ratio,
        issues,
        verb_data["weak_phrases_found"],
        quant
    )
    bar = "█" * (score // 5) + "░" * (20 - score // 5)
    print(f"\n  Score: {score}/100")
    print(f"  [{bar}] {score}%")
    print(f"\n  Grade: {grade}")

    # ── Top Recommendations ──
    print_section("7. TOP RECOMMENDATIONS")
    recs = []

    if jd_tokens and missing:
        top_missing = [kw for kw, _ in missing[:5]]
        recs.append(f"Add missing keywords: {', '.join(top_missing)}")
    if issues:
        recs.append("Fix formatting: " + issues[0])
    if not verb_data["power_verbs_used"]:
        recs.append("Start bullet points with strong verbs: 'Built', 'Shipped', 'Reduced'")
    if quant["numbers_found"] < 3:
        recs.append("Add at least 3 quantified achievements (%, $, x, team size)")
    if verb_data["weak_phrases_found"]:
        recs.append(f"Remove weak phrase: '{verb_data['weak_phrases_found'][0]}'")

    if not recs:
        print("  ✓  Resume looks solid for ATS. Focus on tailoring per job description.")
    else:
        for i, rec in enumerate(recs, 1):
            print(f"  {i}. {rec}")

    print("\n" + "=" * 70)
    print("  Analysis complete - CreatorDockStudio Job Application Tracker PRO")
    print("=" * 70 + "\n")


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    print("\nATS Resume Checker - CreatorDockStudio")
    print("=" * 40)

    # Resume path
    resume_path = input("\nResume file path (.docx / .pdf / .txt): ").strip().strip('"')
    if not os.path.exists(resume_path):
        print(f"File not found: {resume_path}")
        return

    # Optional: Job description
    jd_input = input("Job description file (press Enter to skip): ").strip().strip('"')
    jd_path = jd_input if jd_input and os.path.exists(jd_input) else None

    if not jd_path and jd_input:
        print("Job description file not found — running resume-only analysis.")

    generate_report(resume_path, jd_path)


if __name__ == "__main__":
    main()

"""
Job Description Analyzer
Developer Job Application Tracker PRO - Bonus Script
CreatorDockStudio

Paste or load any job description → instantly get:
  • Required vs nice-to-have skills breakdown
  • Seniority level detection
  • Salary estimate (based on title + skills)
  • Red flags & green flags
  • Tailored cover letter keywords
  • Fit score vs your skill profile
  • Auto-fills your Excel tracker

Usage:
    python job_description_analyzer.py

Requirements:
    pip install openpyxl
"""

import re
import json
import os
from datetime import datetime
from collections import Counter

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


# ─── Knowledge Banks ─────────────────────────────────────────────────────────

SENIORITY_SIGNALS = {
    "intern":    ["intern", "internship", "co-op", "student", "entry level", "0-1 year"],
    "junior":    ["junior", "associate", "entry", "0-2 years", "1-2 years", "new grad", "graduate"],
    "mid":       ["mid", "mid-level", "2-4 years", "3-5 years", "2+ years", "3+ years"],
    "senior":    ["senior", "sr.", "5+ years", "5-8 years", "6+ years", "7+ years", "lead", "principal"],
    "staff":     ["staff", "principal", "distinguished", "10+ years", "architect"],
    "manager":   ["manager", "em", "engineering manager", "tech lead manager", "director"],
}

SALARY_BENCHMARKS = {
    # (min, max) in USD
    "intern":   (40_000,  90_000),
    "junior":   (70_000, 120_000),
    "mid":      (110_000, 160_000),
    "senior":   (150_000, 220_000),
    "staff":    (200_000, 300_000),
    "manager":  (160_000, 260_000),
}

SALARY_ADJUSTERS = {
    # Skills that bump salary estimates
    "machine learning": 15_000,
    "deep learning":    15_000,
    "llm":              20_000,
    "ai":               10_000,
    "kubernetes":       10_000,
    "rust":             12_000,
    "go":                8_000,
    "aws":               8_000,
    "system design":     5_000,
    "distributed":      10_000,
    "real-time":         8_000,
    "blockchain":       10_000,
}

RED_FLAGS = {
    "rockstar developer":      "Vague 'rockstar' language — culture may be toxic",
    "we're a family":          "'We're a family' — common manipulation tactic",
    "fast-paced environment":  "Often means poor planning / constant fire-fighting",
    "unlimited pto":           "Unlimited PTO companies often take less PTO on average",
    "wear many hats":          "Small team stretched thin — you may do roles outside your title",
    "no remote":               "No remote work — geographic restriction",
    "must be available 24/7":  "Unhealthy expectations — work-life balance concern",
    "equity instead of":       "Low base offset with uncertain equity — risk",
    "competitive salary":      "Vague — no actual number given",
    "passion for":             "Passion requirements often mask overwork culture",
    "self-starter":            "Often means no onboarding or mentorship",
    "scrappy":                 "May mean under-resourced or disorganized",
}

GREEN_FLAGS = {
    "remote":               "Remote work offered",
    "4-day work week":      "4-day work week — excellent work-life balance",
    "unlimited pto":        "Flexible time off policy",
    "learning budget":      "Invests in employee development",
    "mentorship":           "Mentorship culture — great for growth",
    "transparent salary":   "Salary range disclosed — company values transparency",
    "diverse":              "Diversity commitment mentioned",
    "open source":          "Open source culture — often innovative environment",
    "conference":           "Conference/event budget offered",
    "401k match":           "Retirement matching — strong benefit",
    "equity":               "Equity/stock offered",
    "flexible":             "Flexible working arrangements",
    "hybrid":               "Hybrid work option",
    "parental leave":       "Parental leave policy — family-friendly",
}

REQUIRED_SIGNALS   = ["required", "must have", "must-have", "you must", "you have", "essential", "minimum"]
PREFERRED_SIGNALS  = ["preferred", "nice to have", "bonus", "plus", "ideally", "desirable", "optional"]

TECH_KEYWORDS = [
    # Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
    "kotlin", "swift", "ruby", "php", "scala", "r", "dart", "bash", "sql",
    # Frontend
    "react", "vue", "angular", "next.js", "nuxt", "svelte", "html", "css",
    "sass", "tailwind", "webpack", "vite", "redux", "graphql",
    # Backend
    "node.js", "express", "django", "flask", "fastapi", "spring", "rails",
    "laravel", "grpc", "rabbitmq", "kafka", "rest api", "microservices",
    # DB
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb",
    "cassandra", "sqlite", "firebase",
    # Cloud / DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible",
    "ci/cd", "jenkins", "github actions", "linux", "nginx",
    # Data / AI
    "machine learning", "deep learning", "pytorch", "tensorflow", "scikit-learn",
    "llm", "nlp", "data pipeline", "spark", "airflow", "pandas", "numpy",
    # Practices
    "agile", "scrum", "tdd", "bdd", "clean code", "solid", "design patterns",
    "system design", "distributed", "real-time", "event-driven",
]


# ─── Parsing Helpers ─────────────────────────────────────────────────────────

def clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9#+./'-]+", text.lower())
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
    trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words) - 2)]
    return words + bigrams + trigrams


def extract_salary_from_text(text: str) -> str | None:
    patterns = [
        r'\$[\d,]+\s*[-–to]+\s*\$[\d,]+',
        r'\$[\d,]+[kK]\s*[-–to]+\s*\$?[\d,]+[kK]',
        r'[\d,]+\s*[-–]\s*[\d,]+\s*(?:USD|usd|per year|annually|\/year|\/yr)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return None


def detect_seniority(tokens: list[str], text: str) -> str:
    text_lower = text.lower()
    scores = {level: 0 for level in SENIORITY_SIGNALS}
    for level, signals in SENIORITY_SIGNALS.items():
        for signal in signals:
            if signal in text_lower:
                scores[level] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "mid"


def extract_tech_skills(tokens: list[str]) -> list[str]:
    token_set = set(tokens)
    return [kw for kw in TECH_KEYWORDS if kw in token_set]


def estimate_salary(seniority: str, skills: list[str]) -> tuple[int, int]:
    base_min, base_max = SALARY_BENCHMARKS.get(seniority, (100_000, 150_000))
    adjustment = sum(SALARY_ADJUSTERS.get(s, 0) for s in skills)
    adjustment = min(adjustment, 40_000)  # cap
    return base_min + adjustment, base_max + adjustment


def split_required_vs_preferred(text: str) -> tuple[list[str], list[str]]:
    """Heuristic: lines near required/preferred signal words."""
    lines = text.split('\n')
    required, preferred = [], []
    mode = "required"  # default assumption

    for line in lines:
        line_lower = line.lower()
        if any(sig in line_lower for sig in REQUIRED_SIGNALS):
            mode = "required"
        elif any(sig in line_lower for sig in PREFERRED_SIGNALS):
            mode = "preferred"

        # Pick lines that look like bullet requirements
        if re.match(r'^\s*[-•*]\s+.{10,}', line):
            if mode == "required":
                required.append(clean(re.sub(r'^[\s\-•*]+', '', line)))
            else:
                preferred.append(clean(re.sub(r'^[\s\-•*]+', '', line)))

    return required, preferred


def check_flags(text: str) -> tuple[list[str], list[str]]:
    text_lower = text.lower()
    reds   = [msg for phrase, msg in RED_FLAGS.items()   if phrase in text_lower]
    greens = [msg for phrase, msg in GREEN_FLAGS.items() if phrase in text_lower]
    return reds, greens


def generate_cover_letter_keywords(jd_skills: list[str], seniority: str) -> list[str]:
    """Return the top keywords to weave into a cover letter."""
    priority = jd_skills[:6]
    base = ["problem-solving", "collaboration", "ownership", "impact"]
    seniority_kw = {
        "junior":  ["eager to learn", "fast learner", "growing"],
        "mid":     ["deliver end-to-end", "independent contributor"],
        "senior":  ["technical leadership", "mentoring", "architecture"],
        "staff":   ["cross-team influence", "org-wide impact"],
        "manager": ["team growth", "roadmap", "stakeholder alignment"],
    }
    return priority + base + seniority_kw.get(seniority, [])


def fit_score(my_skills: list[str], jd_skills: list[str]) -> int:
    if not jd_skills:
        return 50
    matched = len(set(my_skills) & set(jd_skills))
    return min(100, int((matched / len(jd_skills)) * 100))


# ─── Excel Integration ───────────────────────────────────────────────────────

def add_to_excel_tracker(tracker_path: str, company: str, role: str,
                         salary_min: int, source: str, notes: str):
    if not EXCEL_AVAILABLE:
        print("  [!]  openpyxl not installed - skipping Excel update")
        return
    if not os.path.exists(tracker_path):
        print(f"  ⚠  Tracker not found at: {tracker_path}")
        return
    try:
        wb = openpyxl.load_workbook(tracker_path)
        ws = wb["Applications"]
        # Find first empty row
        row = ws.max_row + 1
        # v3.0: Company=col2, Role=col3, Salary=col7, Source=col8, DateApplied=col9, Status=col10, Notes=col33
        ws.cell(row=row, column=2, value=company)
        ws.cell(row=row, column=3, value=role)
        ws.cell(row=row, column=7, value=salary_min)
        ws.cell(row=row, column=8, value=source)
        ws.cell(row=row, column=9, value=datetime.now().strftime("%Y-%m-%d"))
        ws.cell(row=row, column=10, value="Applied")
        ws.cell(row=row, column=33, value=notes[:200] if notes else "")
        wb.save(tracker_path)
        print(f"  ✓  Added to Excel tracker (row {row})")
    except Exception as e:
        print(f"  ⚠  Excel update failed: {e}")


# ─── Report ──────────────────────────────────────────────────────────────────

def print_section(title: str, width: int = 68):
    print(f"\n{'-' * width}")
    print(f"  {title}")
    print(f"{'-' * width}")


def analyze(jd_text: str, my_skills_input: str = "", tracker_path: str = "",
            company_name: str = "", source: str = ""):
    tokens = tokenize(jd_text)

    seniority       = detect_seniority(tokens, jd_text)
    jd_skills       = extract_tech_skills(tokens)
    salary_range    = extract_salary_from_text(jd_text)
    est_min, est_max = estimate_salary(seniority, jd_skills)
    required, preferred = split_required_vs_preferred(jd_text)
    red_flags, green_flags = check_flags(jd_text)

    # Extract company/role from first 3 lines if possible
    first_lines = [l.strip() for l in jd_text.split('\n') if l.strip()][:3]
    jd_title_hint = first_lines[0] if first_lines else "Unknown Role"

    # Fit score
    my_skills = [s.strip().lower() for s in my_skills_input.split(',')] if my_skills_input else []
    score = fit_score(my_skills, jd_skills) if my_skills else None

    # Cover letter keywords
    cl_keywords = generate_cover_letter_keywords(jd_skills, seniority)

    # ── Print Report ──
    print("\n" + "=" * 68)
    print("  JOB DESCRIPTION ANALYZER - CreatorDockStudio")
    print("=" * 68)

    print_section("1. ROLE OVERVIEW")
    print(f"  Detected Seniority : {seniority.upper()}")
    print(f"  Posted Salary      : {salary_range or 'Not listed'}")
    print(f"  Estimated Range    : ${est_min:,} - ${est_max:,} USD/year")

    print_section("2. REQUIRED TECH SKILLS")
    if jd_skills:
        for i, skill in enumerate(jd_skills, 1):
            print(f"  {i:2}. {skill}")
    else:
        print("  No specific tech keywords detected")

    print_section("3. REQUIRED vs PREFERRED (from bullet points)")
    if required:
        print("  REQUIRED:")
        for r in required[:8]:
            print(f"    ✓ {r}")
    if preferred:
        print("\n  NICE TO HAVE:")
        for p in preferred[:6]:
            print(f"    ◦ {p}")
    if not required and not preferred:
        print("  Could not split — paste JD with bullet points for best results")

    if score is not None:
        print_section("4. YOUR FIT SCORE")
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        print(f"  [{bar}] {score}/100")
        if score >= 75:
            print("  → STRONG FIT — apply with confidence")
        elif score >= 50:
            print("  → MODERATE FIT — worth applying, close skill gaps first")
        else:
            print("  → LOW FIT — apply selectively; focus on skill development")

    print_section(f"{'4' if score is None else '5'}. 🚩 RED FLAGS")
    if red_flags:
        for flag in red_flags:
            print(f"  ⚠  {flag}")
    else:
        print("  ✓  No major red flags detected")

    print_section(f"{'5' if score is None else '6'}. ✅ GREEN FLAGS")
    if green_flags:
        for flag in green_flags:
            print(f"  ✓  {flag}")
    else:
        print("  No explicit green flags detected")

    print_section(f"{'6' if score is None else '7'}. ✉  COVER LETTER KEYWORDS")
    print("  Use these naturally in your cover letter:\n")
    print("  " + ", ".join(cl_keywords))

    print_section(f"{'7' if score is None else '8'}. INTERVIEW PREP TOPICS")
    print("  Based on required skills - expect questions on:\n")
    for skill in jd_skills[:8]:
        print(f"  • {skill.title()}")

    # ── Excel auto-fill ──
    if tracker_path:
        print_section("9. EXCEL TRACKER - AUTO FILL")
        company = company_name or jd_title_hint
        source  = source or "Job Board"
        notes   = ", ".join(jd_skills[:5])
        add_to_excel_tracker(tracker_path, company, jd_title_hint, est_min, source, notes)

    print("\n" + "=" * 68)
    print("  Analysis complete - Developer Job Application Tracker PRO")
    print("=" * 68 + "\n")

    return {
        "seniority": seniority,
        "skills": jd_skills,
        "salary_posted": salary_range,
        "salary_estimate": (est_min, est_max),
        "red_flags": red_flags,
        "green_flags": green_flags,
        "fit_score": score,
        "cover_letter_keywords": cl_keywords,
    }


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    print("\nJob Description Analyzer - CreatorDockStudio")
    print("=" * 45)
    print("Paste the full job description below.")
    print("Press Enter twice when done.\n")

    lines = []
    try:
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
    except EOFError:
        pass

    jd_text = "\n".join(lines).strip()

    if not jd_text:
        # Try loading from file
        path = input("\nOr enter path to JD file (.txt): ").strip().strip('"')
        if path and os.path.exists(path):
            with open(path, encoding="utf-8", errors="ignore") as f:
                jd_text = f.read()
        else:
            print("No input provided. Exiting.")
            return

    my_skills = input(
        "\nYour skills (comma-separated, or press Enter to skip):\n> "
    ).strip()

    tracker_path_input = input(
        "\nExcel tracker path (press Enter to skip auto-fill):\n> "
    ).strip().strip('"')

    tracker_path = tracker_path_input if tracker_path_input else ""

    company_name = ""
    source = ""
    if tracker_path:
        company_name = input("\n  Company name: ").strip()
        source = input("  How did you find this job? (e.g. LinkedIn): ").strip() or "Job Board"

    analyze(jd_text, my_skills, tracker_path, company_name, source)


if __name__ == "__main__":
    main()

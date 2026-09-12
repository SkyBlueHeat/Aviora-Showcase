"""
Interview Prep Timer & Scorecard
Developer Job Application Tracker PRO - CreatorDockStudio

Provides a bank of common interview questions by category,
a per-answer timer, and a scorecard saved to JSON.
"""

import json
import os
from datetime import datetime

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SCORES_FILE = os.path.join(DATA_DIR, "interview_scores.json")

QUESTIONS = {
    "Behavioral (STAR)": [
        "Tell me about yourself.",
        "Describe a time you overcame a major challenge at work.",
        "Give an example of a time you showed leadership.",
        "Tell me about a time you failed and what you learned.",
        "Describe a situation where you had to work with a difficult colleague.",
        "Give an example of a time you went above and beyond.",
        "Tell me about a time you had to meet a tight deadline.",
        "Describe a project you're most proud of.",
        "How do you handle conflicting priorities?",
        "Tell me about a time you disagreed with your manager.",
    ],
    "Technical / Problem Solving": [
        "Walk me through how you would debug a production issue at 2 AM.",
        "How do you approach learning a new technology or framework?",
        "Explain the difference between REST and GraphQL APIs.",
        "What is your approach to writing testable code?",
        "How do you ensure code quality in a team environment?",
        "Describe the architecture of a recent system you built.",
        "How would you optimize a slow database query?",
        "What is CI/CD and why does it matter?",
        "Explain the CAP theorem in simple terms.",
        "How do you handle technical debt in a fast-moving team?",
    ],
    "Motivation & Culture Fit": [
        "Why do you want to work here?",
        "Where do you see yourself in 5 years?",
        "What are your greatest strengths?",
        "What is your biggest weakness?",
        "Why are you leaving your current role?",
        "What does your ideal work environment look like?",
        "How do you stay up to date with industry trends?",
        "What motivates you most in your work?",
        "How do you handle feedback and criticism?",
        "What are you looking for in your next role?",
    ],
    "Salary & Logistics": [
        "What are your salary expectations?",
        "Are you interviewing with other companies?",
        "When can you start?",
        "Are you open to relocation or remote work?",
        "Do you have any questions for us?",
    ],
}

SCORE_LABELS = {1: "Poor", 2: "Below Average", 3: "Average", 4: "Good", 5: "Excellent"}
TIPS = {
    "Behavioral (STAR)": "Use the STAR method: Situation → Task → Action → Result.",
    "Technical / Problem Solving": "Think out loud. Explain your reasoning before jumping to the answer.",
    "Motivation & Culture Fit": "Research the company's mission, recent news, and team culture beforehand.",
    "Salary & Logistics": "Know your market rate. Use ranges, not single numbers.",
}

# ── Interviewer personas ──────────────────────────────────────────────────────
INTERVIEWER = {
    "name": "Alex",
    "title": "Senior Hiring Manager",
    "reactions": {
        5: [
            "Excellent answer. That's exactly the kind of structured thinking we look for.",
            "Very impressive. You clearly have solid experience with this.",
            "Great response — specific, concise, and results-oriented.",
        ],
        4: [
            "Good answer. I appreciated the specific example you gave.",
            "Solid response. A bit more detail on the outcome would make it perfect.",
            "Nice work. You covered the key points well.",
        ],
        3: [
            "Decent answer, but I'd like to hear a more concrete example.",
            "You're on the right track. Try to be a bit more specific next time.",
            "Fair response. Adding measurable results would strengthen this significantly.",
        ],
        2: [
            "I appreciate you trying, but the answer lacked specific details.",
            "This needs more structure. Walk me through a real situation next time.",
            "A bit too vague for what we're looking for. Let's keep going.",
        ],
        1: [
            "That didn't quite answer the question. Let's move on and you can come back to it.",
            "I'd like to revisit this one later — try to think of a concrete example.",
            "Very brief. In a real interview, this would raise concerns.",
        ],
    },
    "follow_ups": {
        "Behavioral (STAR)": [
            "What was the measurable outcome of that situation?",
            "How did that experience change your approach going forward?",
            "If you had to do it again, what would you do differently?",
        ],
        "Technical / Problem Solving": [
            "Can you walk me through the trade-offs of that approach?",
            "How would that solution scale to 10x the load?",
            "What would you have done if that approach had failed?",
        ],
        "Motivation & Culture Fit": [
            "How does that align with our company's mission?",
            "Can you give me a concrete example of that in practice?",
            "What does success look like to you in that area?",
        ],
        "Salary & Logistics": [
            "Is that figure flexible depending on the overall package?",
            "What other factors beyond salary are important to you?",
        ],
    },
}

# ── Per-question keyword scoring hints ───────────────────────────────────────
QUESTION_KEYWORDS = {
    "Tell me about yourself.": {
        "required": ["experience", "background", "worked", "role", "years"],
        "bonus":    ["passionate", "skills", "contributed", "built", "led"],
        "star_expected": False,
    },
    "Describe a time you overcame a major challenge at work.": {
        "required": ["challenge", "problem", "solved", "result", "outcome"],
        "bonus":    ["team", "deadline", "learned", "improved", "delivered"],
        "star_expected": True,
    },
    "Give an example of a time you showed leadership.": {
        "required": ["team", "led", "direction", "decision", "outcome"],
        "bonus":    ["motivated", "coached", "aligned", "delivered", "responsibility"],
        "star_expected": True,
    },
    "Tell me about a time you failed and what you learned.": {
        "required": ["failed", "mistake", "learned", "improved", "changed"],
        "bonus":    ["reflection", "growth", "process", "avoid", "next time"],
        "star_expected": True,
    },
    "Describe a situation where you had to work with a difficult colleague.": {
        "required": ["colleague", "conflict", "communication", "resolved", "worked"],
        "bonus":    ["empathy", "understanding", "compromise", "outcome", "relationship"],
        "star_expected": True,
    },
    "Give an example of a time you went above and beyond.": {
        "required": ["extra", "beyond", "initiative", "impact", "delivered"],
        "bonus":    ["proactive", "ownership", "improved", "recognized", "result"],
        "star_expected": True,
    },
    "Tell me about a time you had to meet a tight deadline.": {
        "required": ["deadline", "time", "delivered", "prioritized", "managed"],
        "bonus":    ["pressure", "organized", "communicated", "completed", "shipped"],
        "star_expected": True,
    },
    "Describe a project you're most proud of.": {
        "required": ["project", "built", "achieved", "impact", "result"],
        "bonus":    ["team", "scale", "users", "performance", "challenge"],
        "star_expected": True,
    },
    "How do you handle conflicting priorities?": {
        "required": ["prioritize", "communicate", "stakeholder", "decision", "focus"],
        "bonus":    ["framework", "trade-off", "deadline", "aligned", "transparent"],
        "star_expected": False,
    },
    "Tell me about a time you disagreed with your manager.": {
        "required": ["disagreed", "perspective", "communicated", "respected", "outcome"],
        "bonus":    ["data", "professional", "resolved", "learned", "compromise"],
        "star_expected": True,
    },
    "Walk me through how you would debug a production issue at 2 AM.": {
        "required": ["logs", "monitor", "isolate", "rollback", "communicate"],
        "bonus":    ["alert", "reproduce", "root cause", "post-mortem", "metrics"],
        "star_expected": False,
    },
    "How do you approach learning a new technology or framework?": {
        "required": ["docs", "practice", "project", "learn", "experiment"],
        "bonus":    ["community", "mentor", "hands-on", "apply", "understand"],
        "star_expected": False,
    },
    "Explain the difference between REST and GraphQL APIs.": {
        "required": ["rest", "graphql", "endpoint", "query", "data"],
        "bonus":    ["over-fetching", "schema", "flexibility", "client", "performance"],
        "star_expected": False,
    },
    "What is your approach to writing testable code?": {
        "required": ["test", "unit", "mock", "coverage", "separation"],
        "bonus":    ["tdd", "integration", "dependency injection", "clean", "refactor"],
        "star_expected": False,
    },
    "How do you ensure code quality in a team environment?": {
        "required": ["review", "standards", "ci", "linting", "testing"],
        "bonus":    ["pr", "feedback", "documentation", "automated", "culture"],
        "star_expected": False,
    },
    "Describe the architecture of a recent system you built.": {
        "required": ["architecture", "components", "service", "database", "design"],
        "bonus":    ["scalable", "microservice", "api", "cache", "trade-off"],
        "star_expected": False,
    },
    "How would you optimize a slow database query?": {
        "required": ["index", "query", "explain", "performance", "optimize"],
        "bonus":    ["cache", "n+1", "join", "profiling", "slow log"],
        "star_expected": False,
    },
    "What is CI/CD and why does it matter?": {
        "required": ["continuous", "integration", "deployment", "pipeline", "automate"],
        "bonus":    ["feedback", "quality", "ship", "rollback", "reliability"],
        "star_expected": False,
    },
    "Explain the CAP theorem in simple terms.": {
        "required": ["consistency", "availability", "partition", "trade-off", "distributed"],
        "bonus":    ["network", "database", "choose", "guarantee", "example"],
        "star_expected": False,
    },
    "How do you handle technical debt in a fast-moving team?": {
        "required": ["debt", "balance", "refactor", "prioritize", "communicate"],
        "bonus":    ["sprint", "business", "risk", "visibility", "pay down"],
        "star_expected": False,
    },
    "Why do you want to work here?": {
        "required": ["company", "mission", "product", "team", "opportunity"],
        "bonus":    ["values", "growth", "impact", "culture", "excited"],
        "star_expected": False,
    },
    "Where do you see yourself in 5 years?": {
        "required": ["growth", "skills", "contribute", "role", "learn"],
        "bonus":    ["leadership", "expertise", "company", "impact", "evolve"],
        "star_expected": False,
    },
    "What are your greatest strengths?": {
        "required": ["strength", "example", "skill", "contributed", "result"],
        "bonus":    ["demonstrated", "impact", "team", "problem", "delivered"],
        "star_expected": False,
    },
    "What is your biggest weakness?": {
        "required": ["weakness", "working on", "improving", "aware", "action"],
        "bonus":    ["progress", "feedback", "learned", "better", "specific"],
        "star_expected": False,
    },
    "Why are you leaving your current role?": {
        "required": ["growth", "opportunity", "next step", "challenge", "ready"],
        "bonus":    ["positive", "grateful", "learned", "excited", "new"],
        "star_expected": False,
    },
    "What does your ideal work environment look like?": {
        "required": ["collaboration", "autonomy", "communicate", "team", "support"],
        "bonus":    ["feedback", "transparent", "trust", "flexibility", "learn"],
        "star_expected": False,
    },
    "How do you stay up to date with industry trends?": {
        "required": ["read", "community", "conference", "learn", "follow"],
        "bonus":    ["blog", "podcast", "github", "newsletter", "apply"],
        "star_expected": False,
    },
    "What motivates you most in your work?": {
        "required": ["impact", "problem", "challenge", "create", "contribute"],
        "bonus":    ["ownership", "users", "team", "growth", "meaningful"],
        "star_expected": False,
    },
    "How do you handle feedback and criticism?": {
        "required": ["listen", "reflect", "improve", "open", "act"],
        "bonus":    ["grateful", "specific", "change", "growth", "example"],
        "star_expected": False,
    },
    "What are you looking for in your next role?": {
        "required": ["growth", "challenge", "team", "impact", "opportunity"],
        "bonus":    ["mission", "culture", "learn", "contribute", "long-term"],
        "star_expected": False,
    },
    "What are your salary expectations?": {
        "required": ["range", "research", "market", "open", "experience"],
        "bonus":    ["total", "compensation", "flexible", "value", "discuss"],
        "star_expected": False,
    },
    "Are you interviewing with other companies?": {
        "required": ["yes", "no", "actively", "exploring", "open"],
        "bonus":    ["timeline", "excited", "priority", "process", "fit"],
        "star_expected": False,
    },
    "When can you start?": {
        "required": ["notice", "weeks", "available", "start", "transition"],
        "bonus":    ["flexible", "discuss", "earliest", "accommodate", "ready"],
        "star_expected": False,
    },
    "Are you open to relocation or remote work?": {
        "required": ["open", "flexible", "remote", "relocate", "location"],
        "bonus":    ["hybrid", "timezone", "discuss", "preference", "consider"],
        "star_expected": False,
    },
    "Do you have any questions for us?": {
        "required": ["team", "role", "success", "culture", "next steps"],
        "bonus":    ["challenges", "growth", "feedback", "day-to-day", "expect"],
        "star_expected": False,
    },
}

STAR_KEYWORDS = {
    "situation": ["situation", "context", "working at", "at the time", "we were", "i was", "company", "project"],
    "task":      ["task", "responsible", "challenge was", "goal was", "needed to", "my job", "objective"],
    "action":    ["i decided", "i took", "i implemented", "i led", "i built", "i proposed", "i reached out",
                  "i created", "i worked", "i coordinated", "i contacted", "i fixed", "i developed"],
    "result":    ["result", "outcome", "as a result", "we achieved", "improved", "reduced", "increased",
                  "delivered", "launched", "saved", "grew", "completed", "succeeded", "impact"],
}

VAGUE_PHRASES = [
    "i always", "i never", "i usually", "i think", "maybe", "kind of", "sort of",
    "i guess", "i feel like", "in general", "normally", "typically", "i try to",
    "i believe", "it depends", "sometimes",
]


# ── Core scoring engine ───────────────────────────────────────────────────────

def analyze_answer(question: str, answer: str, category: str, elapsed_s: float = 0) -> dict:
    """
    Offline AI-style answer analysis.
    Returns: score (1-5), breakdown dict, feedback list, follow_up question
    """
    import random
    answer_lower = answer.lower().strip()
    words        = answer_lower.split()
    word_count   = len(words)

    scores = {}
    feedback = []

    # ── 1. Length check ───────────────────────────────────────────────────────
    if word_count < 20:
        scores["length"] = 0
        feedback.append("❌ Too short — a good interview answer should be at least 3-4 sentences.")
    elif word_count < 50:
        scores["length"] = 1
        feedback.append("⚠️  Answer is brief. Try to elaborate more with specific details.")
    elif word_count <= 250:
        scores["length"] = 2
        feedback.append("✓  Good length — concise and on point.")
    elif word_count <= 400:
        scores["length"] = 1
        feedback.append("⚠️  Slightly long. Try to be more concise and focused.")
    else:
        scores["length"] = 0
        feedback.append("❌ Too long — interviewers lose attention after ~2 minutes. Tighten this up.")

    # ── 2. STAR structure (behavioral only) ───────────────────────────────────
    hint = QUESTION_KEYWORDS.get(question, {})
    star_expected = hint.get("star_expected", category == "Behavioral (STAR)")

    if star_expected:
        star_hits = {}
        for component, kws in STAR_KEYWORDS.items():
            star_hits[component] = any(kw in answer_lower for kw in kws)
        hit_count = sum(star_hits.values())

        if hit_count >= 4:
            scores["star"] = 3
            feedback.append("✓  Strong STAR structure detected — Situation, Task, Action, Result all present.")
        elif hit_count == 3:
            scores["star"] = 2
            missing = [k.capitalize() for k, v in star_hits.items() if not v]
            feedback.append(f"⚠️  STAR structure mostly there. Missing: {', '.join(missing)}.")
        elif hit_count == 2:
            scores["star"] = 1
            feedback.append("⚠️  Partial STAR structure. Make sure to include Situation, Task, Action AND Result.")
        else:
            scores["star"] = 0
            feedback.append("❌ No clear STAR structure found. Start with the Situation, then Task, Action, Result.")
    else:
        scores["star"] = 2  # neutral for non-behavioral

    # ── 3. Keyword relevance ──────────────────────────────────────────────────
    required = hint.get("required", [])
    bonus    = hint.get("bonus", [])
    req_hits = sum(1 for kw in required if kw in answer_lower)
    bon_hits = sum(1 for kw in bonus    if kw in answer_lower)

    if required:
        req_ratio = req_hits / len(required)
        if req_ratio >= 0.7:
            scores["keywords"] = 2
            feedback.append(f"✓  Answer covers the key concepts well ({req_hits}/{len(required)} core topics mentioned).")
        elif req_ratio >= 0.4:
            scores["keywords"] = 1
            missing_kws = [kw for kw in required if kw not in answer_lower][:3]
            feedback.append(f"⚠️  Some key concepts missing. Consider mentioning: {', '.join(missing_kws)}.")
        else:
            scores["keywords"] = 0
            missing_kws = [kw for kw in required if kw not in answer_lower][:4]
            feedback.append(f"❌ Answer misses core concepts. Try to include: {', '.join(missing_kws)}.")
        if bon_hits >= 2:
            scores["keywords"] = min(scores["keywords"] + 1, 2)
            feedback.append(f"✓  Bonus: You touched on {bon_hits} advanced points — great depth.")
    else:
        scores["keywords"] = 1

    # ── 4. Vague language detection ────────────────────────────────────────────
    vague_found = [ph for ph in VAGUE_PHRASES if ph in answer_lower]
    if len(vague_found) >= 3:
        scores["clarity"] = 0
        feedback.append(f"❌ Too many vague phrases: '{vague_found[0]}', '{vague_found[1]}'. Use specific examples instead.")
    elif len(vague_found) >= 1:
        scores["clarity"] = 1
        feedback.append(f"⚠️  Slightly vague phrasing ('{vague_found[0]}'). Be more direct and specific.")
    else:
        scores["clarity"] = 2
        feedback.append("✓  Clear and direct language — no vague filler phrases detected.")

    # ── 5. Specificity signals ─────────────────────────────────────────────────
    specificity_signals = ["percent", "%", "$", "team of", "million", "reduced", "increased",
                           "weeks", "months", "days", "users", "customers", "x faster",
                           "x improvement", "deployed", "shipped", "launched"]
    spec_hits = sum(1 for s in specificity_signals if s in answer_lower)
    if spec_hits >= 2:
        scores["specificity"] = 2
        feedback.append("✓  Excellent — you used specific numbers/metrics which makes your answer memorable.")
    elif spec_hits == 1:
        scores["specificity"] = 1
        feedback.append("⚠️  Try adding one more specific metric or number to make the impact tangible.")
    else:
        scores["specificity"] = 0
        feedback.append("⚠️  No measurable results mentioned. Quantify your impact when possible (%, $, time saved).")

    # ── 6. Compute final score (weighted) ─────────────────────────────────────
    raw = (
        scores["length"]      * 2.5 +
        scores["star"]        * 2.5 +
        scores["keywords"]    * 3.0 +
        scores["clarity"]     * 1.5 +
        scores["specificity"] * 1.5
    )
    max_raw = (2 * 2.5) + (3 * 2.5) + (2 * 3.0) + (2 * 1.5) + (2 * 1.5)
    normalized = raw / max_raw   # 0.0 – 1.0
    score = max(1, min(5, round(1 + normalized * 4)))

    # ── 7. Interviewer reaction ────────────────────────────────────────────────
    reaction = random.choice(INTERVIEWER["reactions"][score])
    follow_ups = INTERVIEWER["follow_ups"].get(category, [])
    follow_up  = random.choice(follow_ups) if follow_ups else ""

    # ── 8. Summary line ────────────────────────────────────────────────────────
    summary = _build_summary(score, word_count, scores, star_expected)

    return {
        "score":       score,
        "label":       SCORE_LABELS[score],
        "reaction":    reaction,
        "follow_up":   follow_up,
        "feedback":    feedback,
        "summary":     summary,
        "breakdown":   scores,
        "word_count":  word_count,
        "elapsed_s":   elapsed_s,
    }


def _build_summary(score: int, word_count: int, scores: dict, star_expected: bool) -> str:
    parts = []
    parts.append(f"Score: {score}/5 ({SCORE_LABELS[score]})")
    parts.append(f"Words: {word_count}")
    if star_expected:
        star_ok = scores.get("star", 0) >= 2
        parts.append(f"STAR: {'Yes' if star_ok else 'Needs work'}")
    kw_ok = scores.get("keywords", 0) >= 1
    parts.append(f"Keywords: {'Good' if kw_ok else 'Missing key concepts'}")
    return "  |  ".join(parts)


def load_scores() -> list:
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_score(entry: dict):
    scores = load_scores()
    scores.append(entry)
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)


def get_summary() -> dict:
    scores = load_scores()
    if not scores:
        return {}
    total = len(scores)
    avg = sum(s.get("score", 0) for s in scores) / total
    by_cat = {}
    for s in scores:
        cat = s.get("category", "Unknown")
        by_cat.setdefault(cat, []).append(s.get("score", 0))
    cat_avgs = {c: round(sum(v)/len(v), 1) for c, v in by_cat.items()}
    sessions = sorted({s.get("session_id", "") for s in scores if s.get("session_id")})
    return {
        "total_answers": total,
        "overall_avg": round(avg, 1),
        "by_category": cat_avgs,
        "sessions": len(sessions),
        "last_session": sessions[-1] if sessions else "—",
    }


def get_categories() -> list:
    return list(QUESTIONS.keys())


def get_questions(category: str) -> list:
    return QUESTIONS.get(category, [])


def get_tip(category: str) -> str:
    return TIPS.get(category, "")

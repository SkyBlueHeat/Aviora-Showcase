"""
Cover Letter Generator
Developer Job Application Tracker PRO - CreatorDockStudio

Generates personalized cover letters using OpenAI API.
Falls back to a high-quality template engine if no API key is provided.
"""

import os
import re
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

# ── Template Blocks ────────────────────────────────────────────────────────────

TONE_INTROS = {
    "professional": (
        "I am writing to express my strong interest in the {role} position at {company}. "
        "With {years} of experience in {field}, I am confident that my background aligns "
        "well with your requirements."
    ),
    "enthusiastic": (
        "I was thrilled to discover the {role} opening at {company} — a company whose work "
        "in {field} I have followed closely. With {years} of hands-on experience, I believe "
        "I can make an immediate impact on your team."
    ),
    "concise": (
        "I am applying for the {role} role at {company}. My {years} of experience in {field} "
        "and proven track record make me a strong candidate for this position."
    ),
}

SKILL_SENTENCES = {
    "python":       "I have built production-grade Python applications, including REST APIs, data pipelines, and automation tools.",
    "javascript":   "My JavaScript expertise spans both frontend (React, Vue) and backend (Node.js) development.",
    "react":        "I have delivered React applications used by thousands of users, with a focus on performance and accessibility.",
    "sql":          "I design and optimize SQL databases and have experience with both relational (PostgreSQL, MySQL) and NoSQL systems.",
    "aws":          "I am experienced with AWS cloud infrastructure including EC2, S3, Lambda, and RDS.",
    "docker":       "I containerize applications with Docker and manage deployments via Docker Compose and Kubernetes.",
    "machine learning": "I have built and deployed machine learning models using scikit-learn, PyTorch, and TensorFlow.",
    "git":          "I follow Git best practices including branching strategies, code review, and CI/CD pipelines.",
    "agile":        "I thrive in Agile/Scrum environments and have served as both a developer and sprint facilitator.",
    "leadership":   "I have led cross-functional engineering teams, mentored junior developers, and driven architectural decisions.",
    "communication":"I communicate technical concepts clearly to both technical and non-technical stakeholders.",
    "java":         "I have built enterprise-grade Java applications using Spring Boot, Hibernate, and Maven.",
    "typescript":   "I write strongly typed TypeScript across full-stack applications, reducing runtime errors significantly.",
    "rest api":     "I design and consume RESTful APIs following OpenAPI standards with proper versioning and documentation.",
    "testing":      "I practice TDD and have experience with Jest, pytest, Selenium, and end-to-end test suites.",
}

CLOSINGS = {
    "professional": (
        "I would welcome the opportunity to discuss how my experience can contribute to {company}'s goals. "
        "Thank you for your consideration. I look forward to speaking with you."
    ),
    "enthusiastic": (
        "I would love the chance to bring my energy and expertise to the {company} team. "
        "I am available for an interview at your earliest convenience and am excited about this opportunity!"
    ),
    "concise": (
        "I look forward to discussing this opportunity. Thank you for your time."
    ),
}

# ── Core Functions ─────────────────────────────────────────────────────────────

def extract_skills_from_jd(jd_text: str) -> list[str]:
    """Extract recognizable skill keywords from a job description."""
    jd_lower = jd_text.lower()
    found = [skill for skill in SKILL_SENTENCES if skill in jd_lower]
    # Also extract capitalized tech terms
    extras = re.findall(r'\b(React|Vue|Angular|Node\.js|Django|Flask|FastAPI|'
                        r'Spring|Kubernetes|Terraform|Redis|GraphQL|MongoDB)\b', jd_text)
    found += [e.lower() for e in extras if e.lower() not in found]
    return list(dict.fromkeys(found))[:6]  # top 6, preserve order, no duplicates


def build_skill_paragraph(skills: list[str]) -> str:
    """Turn extracted skills into flowing sentences."""
    sentences = [SKILL_SENTENCES[s] for s in skills if s in SKILL_SENTENCES]
    if not sentences:
        return ("I bring a strong technical background and a track record of delivering "
                "quality software in collaborative, fast-paced environments.")
    return " ".join(sentences[:3])


def generate_offline(company: str, role: str, jd_text: str,
                     your_name: str, years: str, field: str,
                     tone: str = "professional",
                     extra_notes: str = "") -> str:
    """Generate a cover letter using the built-in template engine (no API needed)."""
    tone = tone if tone in TONE_INTROS else "professional"
    skills = extract_skills_from_jd(jd_text)
    today = datetime.now().strftime("%B %d, %Y")

    intro = TONE_INTROS[tone].format(
        role=role, company=company, years=years, field=field
    )
    skill_para = build_skill_paragraph(skills)
    closing = CLOSINGS[tone].format(company=company)

    body_extras = ""
    if extra_notes.strip():
        body_extras = f"\n\n{extra_notes.strip()}"

    letter = f"""{today}

Hiring Manager
{company}

Dear Hiring Manager,

{intro}

{skill_para}{body_extras}

Throughout my career I have consistently delivered results by combining strong technical ability with clear communication and a collaborative mindset. I am passionate about writing clean, maintainable code and contributing to teams that value quality and continuous improvement.

{closing}

Sincerely,
{your_name}
"""
    return letter.strip()


def generate_with_openai(api_key: str, company: str, role: str,
                         jd_text: str, your_name: str, years: str,
                         field: str, tone: str = "professional",
                         extra_notes: str = "") -> str:
    """Generate a cover letter using the OpenAI API."""
    if not OPENAI_AVAILABLE:
        raise ImportError("openai package not installed. Run: pip install openai")

    client = openai.OpenAI(api_key=api_key)

    tone_instruction = {
        "professional": "formal and professional",
        "enthusiastic": "enthusiastic and energetic while still professional",
        "concise":      "concise and direct — no longer than 3 short paragraphs",
    }.get(tone, "professional")

    prompt = f"""Write a {tone_instruction} cover letter for:
- Applicant name: {your_name}
- Years of experience: {years}
- Field/specialty: {field}
- Target role: {role}
- Target company: {company}
- Tone: {tone_instruction}
{f"- Additional notes to include: {extra_notes}" if extra_notes.strip() else ""}

Job description excerpt:
\"\"\"
{jd_text[:1500]}
\"\"\"

Requirements:
- 3-4 paragraphs
- Opening that hooks the reader
- Middle paragraph highlighting 2-3 specific skills from the JD
- Strong closing with a call to action
- No generic filler phrases like "I am a hard worker"
- Sound like a real human, not a robot
- End with: Sincerely, {your_name}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert career coach and professional writer specializing in tech cover letters."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=700,
        temperature=0.75,
    )
    return response.choices[0].message.content.strip()


def generate(company: str, role: str, jd_text: str,
             your_name: str, years: str = "3+", field: str = "software development",
             tone: str = "professional", extra_notes: str = "",
             api_key: str = "") -> str:
    """
    Main entry point. Uses OpenAI if api_key provided, else offline template.
    Returns the finished cover letter as a string.
    """
    print(f"Generating cover letter for: {role} at {company}")
    print(f"Mode: {'AI (OpenAI)' if api_key else 'Template (offline)'}\n")

    if api_key:
        try:
            letter = generate_with_openai(api_key, company, role, jd_text,
                                          your_name, years, field, tone, extra_notes)
            print("[OK] Cover letter generated with OpenAI.")
        except Exception as e:
            print(f"[!] OpenAI failed ({e}), falling back to template mode...")
            letter = generate_offline(company, role, jd_text,
                                      your_name, years, field, tone, extra_notes)
    else:
        letter = generate_offline(company, role, jd_text,
                                  your_name, years, field, tone, extra_notes)
        print("[OK] Cover letter generated (offline template mode).")

    return letter


def save_letter(letter: str, company: str, role: str, output_dir: str) -> str:
    """Save the cover letter as a .txt file and return the path."""
    os.makedirs(output_dir, exist_ok=True)
    safe = re.sub(r'[^a-zA-Z0-9_-]', '_', f"{company}_{role}")
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"CoverLetter_{safe}_{ts}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(letter)
    print(f"Saved: {path}")
    return path


def main():
    _base      = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(_base, "cover_letters")

    letter = generate(
        company    = "Example Corp",
        role       = "Senior Python Developer",
        jd_text    = "We are looking for a Python developer with REST API, Docker, and AWS experience.",
        your_name  = "Your Name",
        years      = "4",
        field      = "backend development",
        tone       = "professional",
    )
    print("\n" + "=" * 60)
    print(letter)
    print("=" * 60)
    save_letter(letter, "Example_Corp", "Senior_Python_Developer", output_dir)


if __name__ == "__main__":
    main()

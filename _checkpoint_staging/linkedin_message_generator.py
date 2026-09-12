"""
LinkedIn Message Generator
Developer Job Application Tracker PRO - CreatorDockStudio

Generates personalized LinkedIn outreach messages for:
- Cold connection requests
- Referral requests
- Follow-up after applying
- Thank-you after interview
- Reconnecting with old contacts
"""

import os
import re
from datetime import datetime

TEMPLATES = {
    "Cold Connection": {
        "description": "Reach out to someone you don't know at a target company.",
        "char_limit": 300,
        "template": """\
Hi {first_name},

I came across your profile while researching {company} and was genuinely impressed by your work in {their_field}.

I'm a {your_role} with {years} years of experience in {your_field} and I'm exploring opportunities at companies like {company}. \
I'd love to connect and learn more about your experience there — no ask, just a genuine conversation.

Thanks for your time!
{your_name}""",
        "short_template": """\
Hi {first_name}, I'm a {your_role} exploring opportunities in {your_field}. \
I admire {company}'s work and would love to connect briefly — just to learn from your experience there. Thanks!""",
    },

    "Referral Request": {
        "description": "Ask a connection to refer you to an open position.",
        "char_limit": 500,
        "template": """\
Hi {first_name},

Hope you're doing well! I noticed that {company} is hiring for a {target_role} role and I'm really excited about it.

Given my {years} years in {your_field} — including work on {highlight} — I believe I'd be a strong fit.

Would you be open to referring me or sharing any insight about the team? Even a quick note to the hiring manager would mean a lot. I'm happy to share my resume and make this as easy as possible for you.

Thank you so much, {first_name}. I really appreciate it!

Best,
{your_name}""",
    },

    "Follow-Up After Applying": {
        "description": "Message a recruiter or hiring manager after submitting an application.",
        "char_limit": 500,
        "template": """\
Hi {first_name},

I recently applied for the {target_role} position at {company} and wanted to reach out directly to express my enthusiasm.

I have {years} years of experience in {your_field} and I'm particularly drawn to {company} because of {reason}. \
I'm confident I can contribute meaningfully from day one.

I'd love the chance to chat if you have a few minutes. Happy to work around your schedule.

Thank you for your time!
{your_name}""",
    },

    "Thank-You After Interview": {
        "description": "Send a thank-you note within 24 hours of an interview.",
        "char_limit": 500,
        "template": """\
Hi {first_name},

Thank you so much for taking the time to speak with me today about the {target_role} role at {company}.

I really enjoyed our conversation — especially the discussion about {highlight}. It reinforced my excitement about the opportunity and the team's direction.

I remain very interested in joining {company} and I look forward to the next steps. Please don't hesitate to reach out if you need anything else from my side.

Thanks again!
{your_name}""",
    },

    "Reconnecting": {
        "description": "Reach out to an old colleague or contact you've lost touch with.",
        "char_limit": 400,
        "template": """\
Hi {first_name},

It's been a while — hope you've been well! I was thinking about our time at {shared_context} and wanted to reconnect.

I'm currently exploring new opportunities in {your_field} and would love to catch up and hear what you've been up to.

Would you be open to a quick 15-minute call sometime?

Best,
{your_name}""",
    },
}


def generate(
    message_type: str,
    your_name: str,
    your_role: str,
    your_field: str,
    years: str,
    first_name: str,
    company: str,
    target_role: str = "",
    their_field: str = "",
    highlight: str = "",
    reason: str = "",
    shared_context: str = "",
    use_short: bool = False,
) -> str:
    tmpl_data = TEMPLATES.get(message_type)
    if not tmpl_data:
        return f"[Error] Unknown message type: {message_type}"

    template = tmpl_data.get("short_template" if use_short else "template",
                              tmpl_data["template"])

    placeholders = dict(
        your_name=your_name or "Your Name",
        your_role=your_role or "Software Developer",
        your_field=your_field or "software development",
        years=years or "3",
        first_name=first_name or "there",
        company=company or "the company",
        target_role=target_role or "the open role",
        their_field=their_field or "tech",
        highlight=highlight or "my recent projects",
        reason=reason or "its innovative approach",
        shared_context=shared_context or "our previous workplace",
    )

    try:
        message = template.format(**placeholders)
    except KeyError as e:
        message = f"[Error] Missing field: {e}\n\n{template}"

    return message.strip()


def get_message_types() -> list:
    return list(TEMPLATES.keys())


def get_description(message_type: str) -> str:
    return TEMPLATES.get(message_type, {}).get("description", "")


def get_char_limit(message_type: str) -> int:
    return TEMPLATES.get(message_type, {}).get("char_limit", 300)


def save_message(message_type: str, message: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    safe_type = re.sub(r"[^a-zA-Z0-9_]", "_", message_type)
    filename = f"LinkedIn_{safe_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(message)
    return path



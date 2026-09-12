"""
Salary Negotiation Calculator
Developer Job Application Tracker PRO - CreatorDockStudio

Calculates:
- Total compensation breakdown (base, bonus, equity, benefits)
- Counter-offer strategy with walk-away point
- Take-home estimate after tax
- Comparison between multiple offers
"""

# ── Market data (rough US/EU tech benchmarks) ─────────────────────────────────
MARKET_DATA = {
    "Junior (0-2 yrs)":    {"low": 55_000,  "mid": 75_000,  "high": 95_000},
    "Mid-Level (3-5 yrs)": {"low": 85_000,  "mid": 110_000, "high": 140_000},
    "Senior (6-9 yrs)":    {"low": 120_000, "mid": 155_000, "high": 200_000},
    "Staff / Lead (10+)":  {"low": 160_000, "mid": 210_000, "high": 280_000},
    "Principal / Director":{"low": 200_000, "mid": 270_000, "high": 380_000},
}

COST_OF_LIVING = {
    "San Francisco / NYC":  1.0,
    "Seattle / Boston":     0.92,
    "Austin / Denver":      0.78,
    "Remote (US Average)":  0.75,
    "London (UK)":          0.85,
    "Berlin / Amsterdam":   0.70,
    "Istanbul / Eastern EU":0.40,
}

TAX_BRACKETS = {
    "USA (Federal ~24%)":   0.24,
    "USA (Federal ~32%)":   0.32,
    "UK (~40%)":            0.40,
    "Germany (~42%)":       0.42,
    "Netherlands (~49%)":   0.49,
    "Turkey (~27%)":        0.27,
    "No Tax / Flat 20%":    0.20,
}


def calculate_total_comp(
    base: float,
    bonus_pct: float = 0.0,
    equity_annual: float = 0.0,
    signing_bonus: float = 0.0,
    benefits_value: float = 12_000,
) -> dict:
    bonus_amount  = base * (bonus_pct / 100)
    cash_comp     = base + bonus_amount + signing_bonus / 4
    total_comp    = cash_comp + equity_annual + benefits_value

    return {
        "base":             base,
        "bonus":            bonus_amount,
        "bonus_pct":        bonus_pct,
        "equity_annual":    equity_annual,
        "signing_annual":   signing_bonus / 4,
        "benefits":         benefits_value,
        "total_cash":       base + bonus_amount,
        "total_comp":       total_comp,
    }


def calculate_takehome(gross: float, tax_rate: float) -> dict:
    tax        = gross * tax_rate
    net_annual = gross - tax
    net_monthly = net_annual / 12
    return {
        "gross":       gross,
        "tax":         tax,
        "tax_rate":    tax_rate,
        "net_annual":  net_annual,
        "net_monthly": net_monthly,
    }


def negotiation_strategy(
    offer_base: float,
    your_target: float,
    walk_away: float,
    level: str,
    location: str,
) -> dict:
    col_factor = COST_OF_LIVING.get(location, 0.75)
    market     = MARKET_DATA.get(level, MARKET_DATA["Mid-Level (3-5 yrs)"])

    adjusted_mid  = market["mid"] * col_factor
    adjusted_high = market["high"] * col_factor

    gap           = your_target - offer_base
    counter_offer = min(your_target * 1.10, adjusted_high)
    counter_offer = max(counter_offer, your_target)

    if offer_base >= your_target:
        verdict = "GREAT OFFER — at or above your target."
        action  = "Accept or negotiate equity/signing bonus."
    elif offer_base >= walk_away:
        verdict = "ACCEPTABLE — below target but above walk-away."
        action  = f"Counter at ${counter_offer:,.0f}. Worst case, accept the original offer."
    else:
        verdict = "BELOW WALK-AWAY — do not accept as-is."
        action  = "Decline or request a significant raise. Market supports your ask."

    return {
        "offer":          offer_base,
        "your_target":    your_target,
        "walk_away":      walk_away,
        "counter_offer":  counter_offer,
        "gap":            gap,
        "market_mid":     adjusted_mid,
        "market_high":    adjusted_high,
        "verdict":        verdict,
        "action":         action,
    }


def compare_offers(offers: list) -> list:
    """
    offers: list of dicts with keys:
        company, base, bonus_pct, equity_annual, signing_bonus, benefits, tax_rate
    Returns sorted list with total_comp and rank.
    """
    results = []
    for o in offers:
        comp = calculate_total_comp(
            base=o.get("base", 0),
            bonus_pct=o.get("bonus_pct", 0),
            equity_annual=o.get("equity_annual", 0),
            signing_bonus=o.get("signing_bonus", 0),
            benefits_value=o.get("benefits", 12_000),
        )
        th = calculate_takehome(comp["total_cash"], o.get("tax_rate", 0.24))
        results.append({
            "company":      o.get("company", "Company"),
            "total_comp":   comp["total_comp"],
            "total_cash":   comp["total_cash"],
            "net_monthly":  th["net_monthly"],
            "breakdown":    comp,
        })
    results.sort(key=lambda x: x["total_comp"], reverse=True)
    for i, r in enumerate(results): r["rank"] = i + 1
    return results


def get_levels() -> list:
    return list(MARKET_DATA.keys())


def get_locations() -> list:
    return list(COST_OF_LIVING.keys())


def get_tax_options() -> list:
    return list(TAX_BRACKETS.keys())


def get_tax_rate(label: str) -> float:
    return TAX_BRACKETS.get(label, 0.24)

"""
services/chatbot_service.py — Interactive HealthBridge Community Assistant.

Provides fast, contextual, offline responses about:
- HealthBridge project scope, architecture, and SDG 3 & SDG 10 mapping
- The logged-in user's live metrics, scores, trends, records, and recommendations
- Scoring formulas, moving average math, and sliding-window rules
- OOP architecture, validation lab edge cases, and persona profiles
- Strict non-medical ethical disclaimers
"""

from __future__ import annotations
import re
from typing import Optional, Mapping, Any

PROJECT_KEYWORDS = {
    "healthbridge", "health bridge", "wellbeing", "well-being", "lifestyle",
    "tracker", "record", "records", "sleep", "activity", "water", "hydration",
    "mood", "stress", "score", "composite", "trend", "trends", "sliding window",
    "recommendation", "recommendations", "sdg", "sdg 3", "sdg 10", "oop",
    "validation", "duplicate", "export", "csv", "json", "moving average",
    "persona", "asha", "rohan", "priya", "marcus", "admin", "weight", "target",
    "disclaimer", "non-medical", "coach", "goals", "what-if", "simulator"
}


def get_chatbot_response(query: str, user_context: Optional[Mapping[str, Any]] = None) -> str:
    """
    Generate an intelligent response given user query and authenticated session context.
    """
    raw_query = query.strip()
    if not raw_query:
        return "Please ask a question about HealthBridge, your wellness records, scores, or SDG 3 & 10."

    q = raw_query.lower()

    # Context extraction if user is logged in
    has_ctx = user_context is not None and bool(user_context.get("user_id"))
    full_name = user_context.get("full_name", "Friend") if has_ctx else "Guest"
    record_count = user_context.get("record_count", 0) if has_ctx else 0
    overall_score = user_context.get("overall_score", 0.0) if has_ctx else 0.0
    score_band = user_context.get("score_band", "Unscored") if has_ctx else "Unscored"
    averages = user_context.get("averages", {}) if has_ctx else {}
    avg_sleep = averages.get("sleep", 0.0)
    avg_activity = averages.get("activity", 0.0)
    avg_water = averages.get("water", 0.0)
    avg_mood = averages.get("mood", 0.0)
    avg_stress = averages.get("stress", 0.0)
    recs = user_context.get("recommendations", []) if has_ctx else []
    trends = user_context.get("trends", {}) if has_ctx else {}

    # 1. Greetings & Identity
    if re.search(r"^\s*(hi|hello|hey|namaste|greetings|good\s*(morning|afternoon|evening))\b", q):
        if has_ctx:
            return (
                f"Hello {full_name}! 👋 I am your HealthBridge Assistant.\n\n"
                f"You currently have {record_count} recorded days with an overall Wellness Index of {overall_score:.1f} ({score_band}).\n"
                "You can ask me about your scores, trends, non-medical recommendations, or how our OOP algorithms work!"
            )
        return (
            "Hello! 👋 I am the HealthBridge Assistant for HACK-AI-THON 2026.\n"
            "I can explain our community wellness platform, SDG 3 & 10 alignment, scoring formulas, "
            "and demonstration personas. What would you like to know?"
        )

    if re.search(r"\b(who are you|what are you|your name)\b", q):
        return (
            "I am the HealthBridge Assistant, an explainable lifestyle guide built for the "
            "HACK-AI-THON 2026 National Level Group Challenge.\n\n"
            "I provide transparent insight into your self-reported wellness records, sliding-window "
            "trends, scoring formulas, and SDG 3 & 10 community health equity initiatives."
        )

    if re.search(r"\b(how are you|how r u)\b", q):
        return (
            "I'm operating at peak performance! Ready to analyze your lifestyle habits, "
            "explain sliding-window trends, or answer questions about our OOP architecture. How can I help you today?"
        )

    if re.search(r"\b(thank(s| you)?|thx|ty|great|awesome)\b", q):
        return "You're very welcome! Let me know if you need any other insights into your health patterns or system features."

    # 2. Disclaimer / Non-Medical Guardrails
    if re.search(r"\b(medical|diagnosis|doctor|prescribe|clinical|pathology|cure|disease|treatment)\b", q):
        return (
            "⚠️ MANDATORY NON-MEDICAL DISCLAIMER:\n\n"
            "HealthBridge is strictly an educational self-reflection and lifestyle tracking tool. "
            "It does NOT diagnose medical conditions, evaluate clinical pathology, or prescribe treatments.\n\n"
            "All recommendations are non-medical lifestyle reflections (e.g. hydration pacing, walking breaks, sleep hygiene). "
            "Anyone experiencing clinical symptoms should always consult a licensed medical professional."
        )

    # 3. User Specific Live Metrics Queries
    if re.search(r"\b(how many records|record count|my entries|total records|logged days)\b", q):
        if not has_ctx:
            return "Please log in with one of our demo personas or your account to view your recorded days."
        return (
            f"You have logged {record_count} daily wellness records in your account.\n"
            f"These entries span 14 days of tracked sleep, physical movement, hydration, mood, and stress."
        )

    if re.search(r"\b(my score|overall score|wellness score|wellness index|what is my score)\b", q):
        if not has_ctx:
            return "Please log in to view your current composite score."
        return (
            f"Your current Composite Wellness Score is {overall_score:.1f} / 100 ({score_band}).\n\n"
            "Point contributions based on current targets:\n"
            f"• Sleep (40% max): evaluated from your {avg_sleep:.1f}h daily average\n"
            f"• Activity (35% max): evaluated from your {avg_activity:.0f}m daily average\n"
            f"• Water (25% max): evaluated from your {avg_water:.1f}L daily average\n"
            f"• Mood bonus & stress penalty applied dynamically."
        )

    if re.search(r"\b(my averages|average sleep|average water|average activity|my stats|how am i doing)\b", q):
        if not has_ctx:
            return "Please log in to view your 7-day rolling averages."
        return (
            f"Here is your 7-day lifestyle summary ({full_name}):\n\n"
            f"• Sleep Duration:   {avg_sleep:.1f} hours / day (Target: 8.0h)\n"
            f"• Physical Activity:{avg_activity:.0f} minutes / day (Target: 30m)\n"
            f"• Hydration Intake: {avg_water:.1f} Litres / day (Target: 2.0L)\n"
            f"• Mood Rating:      {avg_mood:.1f} / 5.0\n"
            f"• Stress Level:     {avg_stress:.1f} / 5.0 (Lower is better)\n\n"
            f"Current Score: {overall_score:.1f} ({score_band})."
        )

    if re.search(r"\b(recommendation|suggestions|how to improve|how can i improve|improve my score|next step)\b", q):
        if not has_ctx or not recs:
            return (
                "To improve your lifestyle score:\n"
                "1. Aim for 7–9 hours of consistent sleep (40% of score weight).\n"
                "2. Reach 30+ minutes of daily moderate movement (35% weight).\n"
                "3. Maintain 2.0+ Litres of daily tap water hydration (25% weight).\n"
                "4. Incorporate wind-down breathing to lower daily stress levels."
            )
        rec_lines = []
        for r in recs[:3]:
            rec_lines.append(f"• Priority {r.get('priority', 1)} [{r.get('indicator', '').replace('_', ' ').title()}]: {r.get('suggestion')} (Reason: {r.get('reason')})")
        return "Here are your prioritized, non-medical lifestyle recommendations:\n\n" + "\n\n".join(rec_lines)

    if re.search(r"\b(my trend|detected trend|trends for me|is my sleep improving)\b", q):
        if not has_ctx or not trends:
            return "Log into your account to see your real-time sliding-window trend classifications."
        t_lines = []
        for ind, tinfo in trends.items():
            t_lines.append(f"• {ind.replace('_', ' ').title()}: {tinfo.get('classification', '').title()} ({tinfo.get('percentage_change', 0):+.1f}%) — {tinfo.get('reason', '')}")
        return "Here is your sliding-window trend analysis:\n\n" + "\n\n".join(t_lines)

    # 4. Methodology & Mathematical Rules
    if re.search(r"\b(how is (the )?score calculated|scoring formula|weights|weighted)\b", q):
        return (
            "The HealthBridge Composite Wellness Score (0–100) is calculated via configurable weights:\n\n"
            "1. Base Score (100 pts total):\n"
            "   • Sleep Duration:   40% (Target: 8.0 hrs) -> (hours / 8.0) * 40, capped at 40\n"
            "   • Physical Activity:35% (Target: 30 mins) -> (minutes / 30) * 35, capped at 35\n"
            "   • Water Hydration:  25% (Target: 2.0 L)   -> (litres / 2.0) * 25, capped at 25\n\n"
            "2. Subjective Modifiers:\n"
            "   • Mood Bonus:   +((mood - 3) * 2.5) for ratings > 3 (up to +5 pts)\n"
            "   • Stress Penalty: -((stress - 3) * 2.5) for stress > 3 (up to -5 pts)\n\n"
            "Final Composite Score = Clamp(Base Score + Mood Bonus - Stress Penalty, 0, 100)."
        )

    if re.search(r"\b(sliding window|trend detection|how do trends work|rule[- ]based trends)\b", q):
        return (
            "HealthBridge uses a sliding-window rule-based trend classification algorithm:\n\n"
            "• Method: Compares the average of the most recent 3 days against the preceding 3-day window.\n"
            "• Percentage Change Formula: ((Recent Window Avg - Prior Window Avg) / Prior Window Avg) * 100\n\n"
            "Classification Rules:\n"
            "1. Sustained Improvement: Percentage change > +10%\n"
            "2. Sustained Decline:     Percentage change < -10%\n"
            "3. Stagnant / Stable:     Percentage change between -5% and +5%\n"
            "4. Sudden Variation:      Single-day shift > 25% away from baseline."
        )

    if re.search(r"\b(moving average|3-day average|7-day average|smoothing)\b", q):
        return (
            "A 3-day moving average smooths out daily variance (such as an unusually late night or a single intense workout day).\n\n"
            "Formula for Day t: MA_3 = (Day[t] + Day[t-1] + Day[t-2]) / 3.\n"
            "This provides a stable trend line in our Chart.js analytics without obscuring genuine lifestyle shifts."
        )

    # 5. SDG Alignment
    if re.search(r"\b(sdg|sustainable development|sdg 3|sdg 10|good health|reduced inequalities)\b", q):
        return (
            "HealthBridge is built in direct alignment with two UN Sustainable Development Goals:\n\n"
            "🎯 SDG 3: Good Health & Well-Being (Target 3.4)\n"
            "Promotes early personal reflection on non-communicable lifestyle risk factors (sleep debt, sedentary routines, chronic dehydration) before clinical intervention is needed.\n\n"
            "🎯 SDG 10: Reduced Inequalities (Target 10.2)\n"
            "Eliminates health tracking barriers by focusing exclusively on ZERO-COST, universally accessible habits (neighborhood walking, tap water hydration, sleep routine) rather than requiring $300+ wearable trackers or premium fitness subscriptions."
        )

    # 6. OOP Architecture
    if re.search(r"\b(oop|object oriented|classes|architecture|design patterns?|strategy pattern|inheritance)\b", q):
        return (
            "HealthBridge demonstrates production-grade Object-Oriented Programming (OOP) in Python:\n\n"
            "1. Encapsulation: `WellnessRecord` and `User` enforce internal invariant validation before state changes.\n"
            "2. Composition: `WellnessReport` HAS-A `User`, HAS-A `WellnessScorer`, HAS-A `TrendDetector`, and HAS-A `RecommendationEngine`.\n"
            "3. Polymorphism & Strategy Pattern: `BaseRecommendationStrategy` with derived strategies (`SleepRecommendation`, `ActivityRecommendation`, `HydrationRecommendation`, etc.).\n"
            "4. Inheritance: `BaseExporter` abstracts serialization, inherited by `JSONExporter` and `CSVExporter`.\n"
            "5. Dynamic Configuration: `ScoringConfig` allows dynamic runtime reweighting of indicators."
        )

    # 7. Validation Rules & Validation Lab
    if re.search(r"\b(validation|validation lab|invalid|negative|duplicate|error handling|edge cases?)\b", q):
        return (
            "HealthBridge enforces strict data integrity rules:\n\n"
            "• Sleep Duration:   Must be float between 0.0 and 24.0 hours (rejects negative & >24h).\n"
            "• Physical Activity:Must be integer >= 0 minutes (rejects negative values).\n"
            "• Hydration Intake: Must be float > 0.0 Litres (rejects zero & negative values).\n"
            "• Mood & Stress:    Must be integers within 1–5 range.\n"
            "• Duplicate Dates:  User.add_record() rejects multiple entries for the same calendar date.\n"
            "• Missing Dates:    Rejects empty or malformed date formats.\n\n"
            "🧪 Try them live in our Validation Lab at /validation-lab!"
        )

    # 8. Personas & Demo Accounts
    if re.search(r"\b(persona|personas|jivraj|vaibhav|alex|asha|rohan|priya|marcus|demo accounts?|test users?|admin accounts?)\b", q):
        return (
            "HealthBridge provides pre-seeded evaluator and governance accounts:\n\n"
            "1. Jivraj (`admin_jivraj`) — Lead System Administrator with full role management governance.\n"
            "2. Vaibhav (`admin_vaibhav`) — Co-System Administrator with platform oversight.\n"
            "3. Demo Profile (`trial_demo`) — Pre-loaded with 14 days of realistic sample lifestyle data labeled [Demo Data].\n\n"
            "💡 You can explore safely via the 'Try a Demo Account' button on /login, or sign in as an Administrator."
        )

    # 9. Exports
    if re.search(r"\b(export|csv|json|download|report export)\b", q):
        return (
            "HealthBridge generates comprehensive weekly reports exportable in two formats:\n\n"
            "1. Structured JSON: Complete payload with metadata, period averages, week-over-week changes, trend analysis, daily breakdowns, recommendations, and disclaimer.\n"
            "2. Tabular CSV: Clean rows with daily metrics, trend classifications, and actionable suggestions.\n\n"
            "Download them from the Weekly Reports page (/reports) or run `python main.py --cli`."
        )

    # 10. What-If Simulator
    if re.search(r"\b(simulator|what-if|what if|predict)\b", q):
        return (
            "The interactive 'What-If' Lifestyle Predictor is located on the Health Intelligence page (/intelligence).\n\n"
            "It allows you to slide sleep, physical activity, and hydration sliders to predict your composite wellness index in real-time before logging your actual day!"
        )

    # Fallback / General overview
    return (
        "I can answer questions regarding HealthBridge:\n\n"
        "• Your Metrics: 'What is my score?', 'How many records do I have?', 'What are my recommendations?'\n"
        "• Mathematics: 'How is the score calculated?', 'How does sliding-window trend detection work?'\n"
        "• SDGs & Ethics: 'What SDGs does HealthBridge support?', 'Why is this non-medical?'\n"
        "• Engineering: 'How is OOP implemented?', 'What are the validation rules?', 'Who are the demo personas?'\n\n"
        "What would you like to explore?"
    )

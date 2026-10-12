"""
sample_data.py — Representative multi-user test data for HealthBridge.

Includes:
    1. Asha (Active Improver):
       - 14 days of data showing steady improvement in sleep and activity.
    2. Rohan (Sedentary Desk Worker):
       - 14 days showing low activity, low hydration, and high stress.
    3. Priya (Inconsistent / Stressed Student):
       - 14 days showing volatile sleep and a sudden drop in hydration during exams.
    4. Invalid Data Scenarios:
       - Negative sleep
       - Duplicate date
       - Out-of-range mood
       - Empty date
       - Extreme activity minutes
"""

from models.user import User
from models.wellness_record import WellnessRecord


def build_sample_users() -> dict[str, User]:
    """Create and return a dictionary of 3 users with 14 days of data each."""

    # ------------------------------------------------------------------
    # User 1: Asha — starts modest, improves over 2 weeks
    # ------------------------------------------------------------------
    asha = User(name="Asha Sharma", user_id="asha_sharma")
    asha_records = [
        # Week 1: Baseline
        WellnessRecord("2026-09-28", 6.0, 15, 1.2, mood_rating=3, stress_level=4),
        WellnessRecord("2026-09-29", 6.5, 20, 1.4, mood_rating=3, stress_level=3),
        WellnessRecord("2026-09-30", 5.5, 10, 1.0, mood_rating=2, stress_level=4),
        WellnessRecord("2026-10-01", 6.0, 25, 1.5, mood_rating=3, stress_level=3),
        WellnessRecord("2026-10-02", 6.5, 20, 1.3, mood_rating=3, stress_level=3),
        WellnessRecord("2026-10-03", 7.0, 30, 1.8, mood_rating=4, stress_level=2),
        WellnessRecord("2026-10-04", 7.0, 35, 1.7, mood_rating=4, stress_level=2),
        # Week 2: Clear Improvement
        WellnessRecord("2026-10-05", 7.5, 35, 2.0, mood_rating=4, stress_level=2),
        WellnessRecord("2026-10-06", 7.5, 40, 2.1, mood_rating=4, stress_level=2),
        WellnessRecord("2026-10-07", 8.0, 45, 2.2, mood_rating=5, stress_level=1),
        WellnessRecord("2026-10-08", 7.5, 40, 2.0, mood_rating=4, stress_level=2),
        WellnessRecord("2026-10-09", 8.0, 50, 2.3, mood_rating=5, stress_level=1),
        WellnessRecord("2026-10-10", 8.0, 45, 2.2, mood_rating=5, stress_level=1),
        WellnessRecord("2026-10-11", 8.5, 60, 2.5, mood_rating=5, stress_level=1),
    ]
    for r in asha_records:
        asha.add_record(r)

    # ------------------------------------------------------------------
    # User 2: Rohan — sedentary, low water, elevated stress
    # ------------------------------------------------------------------
    rohan = User(name="Rohan Patel", user_id="rohan_patel")
    rohan_records = [
        # Week 1
        WellnessRecord("2026-09-28", 5.5, 10, 1.0, mood_rating=2, stress_level=4),
        WellnessRecord("2026-09-29", 5.0, 5,  0.8, mood_rating=2, stress_level=5),
        WellnessRecord("2026-09-30", 6.0, 15, 1.1, mood_rating=3, stress_level=4),
        WellnessRecord("2026-10-01", 5.5, 10, 0.9, mood_rating=2, stress_level=4),
        WellnessRecord("2026-10-02", 5.0, 5,  1.0, mood_rating=2, stress_level=5),
        WellnessRecord("2026-10-03", 6.5, 15, 1.2, mood_rating=3, stress_level=3),
        WellnessRecord("2026-10-04", 6.0, 10, 1.1, mood_rating=3, stress_level=4),
        # Week 2: Persistent Lows
        WellnessRecord("2026-10-05", 5.5, 10, 1.0, mood_rating=2, stress_level=4),
        WellnessRecord("2026-10-06", 5.0, 5,  0.8, mood_rating=2, stress_level=5),
        WellnessRecord("2026-10-07", 5.5, 8,  0.9, mood_rating=2, stress_level=4),
        WellnessRecord("2026-10-08", 5.0, 10, 1.0, mood_rating=2, stress_level=5),
        WellnessRecord("2026-10-09", 6.0, 12, 1.1, mood_rating=3, stress_level=4),
        WellnessRecord("2026-10-10", 6.5, 15, 1.3, mood_rating=3, stress_level=3),
        WellnessRecord("2026-10-11", 5.5, 10, 1.0, mood_rating=2, stress_level=4),
    ]
    for r in rohan_records:
        rohan.add_record(r)

    # ------------------------------------------------------------------
    # User 3: Priya — volatile, sudden drop during exam week
    # ------------------------------------------------------------------
    priya = User(name="Priya Nair", user_id="priya_nair")
    priya_records = [
        # Week 1: Good Baseline
        WellnessRecord("2026-09-28", 7.5, 30, 2.0, mood_rating=4, stress_level=2),
        WellnessRecord("2026-09-29", 8.0, 35, 2.2, mood_rating=4, stress_level=2),
        WellnessRecord("2026-09-30", 7.0, 25, 1.8, mood_rating=3, stress_level=3),
        WellnessRecord("2026-10-01", 7.5, 30, 2.0, mood_rating=4, stress_level=2),
        WellnessRecord("2026-10-02", 7.0, 20, 1.7, mood_rating=3, stress_level=3),
        WellnessRecord("2026-10-03", 8.0, 40, 2.3, mood_rating=4, stress_level=2),
        WellnessRecord("2026-10-04", 8.5, 45, 2.5, mood_rating=5, stress_level=1),
        # Week 2: Exam stress — sudden drops
        WellnessRecord("2026-10-05", 6.0, 20, 1.5, mood_rating=3, stress_level=3),
        WellnessRecord("2026-10-06", 4.5, 10, 1.0, mood_rating=2, stress_level=5),
        WellnessRecord("2026-10-07", 4.0, 5,  0.7, mood_rating=1, stress_level=5), # sudden plunge
        WellnessRecord("2026-10-08", 5.0, 10, 0.9, mood_rating=2, stress_level=4),
        WellnessRecord("2026-10-09", 6.0, 15, 1.2, mood_rating=3, stress_level=4),
        WellnessRecord("2026-10-10", 7.0, 25, 1.8, mood_rating=3, stress_level=3),
        WellnessRecord("2026-10-11", 7.5, 30, 2.0, mood_rating=4, stress_level=2),
    ]
    for r in priya_records:
        priya.add_record(r)

    # ------------------------------------------------------------------
    # User 4: Alex Rivera (Trial / Demo Profile) — Clearly Identified Demo Data
    # ------------------------------------------------------------------
    demo = User(name="Alex Rivera (Demo Profile)", user_id="trial_demo")
    demo_records = [
        WellnessRecord("2026-09-28", 7.0, 25, 1.8, mood_rating=4, stress_level=2, notes="[Demo Data] Baseline day"),
        WellnessRecord("2026-09-29", 7.5, 30, 2.0, mood_rating=4, stress_level=2, notes="[Demo Data] Evening walk"),
        WellnessRecord("2026-09-30", 6.5, 20, 1.6, mood_rating=3, stress_level=3, notes="[Demo Data] Hydration check"),
        WellnessRecord("2026-10-01", 7.0, 30, 2.0, mood_rating=4, stress_level=2, notes="[Demo Data] Rest day"),
        WellnessRecord("2026-10-02", 7.5, 35, 2.1, mood_rating=4, stress_level=2, notes="[Demo Data] Consistent sleep"),
        WellnessRecord("2026-10-03", 8.0, 40, 2.3, mood_rating=5, stress_level=1, notes="[Demo Data] Active weekend"),
        WellnessRecord("2026-10-04", 8.0, 45, 2.2, mood_rating=5, stress_level=1, notes="[Demo Data] Park jog"),
        WellnessRecord("2026-10-05", 7.5, 30, 2.0, mood_rating=4, stress_level=2, notes="[Demo Data] Weekday routine"),
        WellnessRecord("2026-10-06", 8.0, 35, 2.2, mood_rating=4, stress_level=2, notes="[Demo Data] High hydration"),
        WellnessRecord("2026-10-07", 7.5, 30, 2.0, mood_rating=4, stress_level=2, notes="[Demo Data] Good rest"),
        WellnessRecord("2026-10-08", 8.0, 40, 2.4, mood_rating=5, stress_level=1, notes="[Demo Data] Mindful breathing"),
        WellnessRecord("2026-10-09", 7.5, 35, 2.1, mood_rating=4, stress_level=2, notes="[Demo Data] Evening stretch"),
        WellnessRecord("2026-10-10", 8.0, 45, 2.3, mood_rating=5, stress_level=1, notes="[Demo Data] Weekend hike"),
        WellnessRecord("2026-10-11", 8.5, 50, 2.5, mood_rating=5, stress_level=1, notes="[Demo Data] Target achievement"),
    ]
    for r in demo_records:
        demo.add_record(r)

    return {
        "asha": asha,
        "rohan": rohan,
        "priya": priya,
        "trial_demo": demo,
        "demo": demo,
        "asha_sharma": asha,
        "rohan_patel": rohan,
        "priya_nair": priya,
    }


def get_invalid_sample_records() -> list[dict]:
    """Return raw record dictionaries representing various failure modes.

    Used by the demonstration to showcase robust input validation.
    """
    return [
        {
            "description": "Negative sleep hours",
            "record": WellnessRecord("2026-10-12", -2.5, 30, 2.0),
            "expected_error": "Sleep must be between 0 and 24 hours",
        },
        {
            "description": "Sleep exceeds 24 hours",
            "record": WellnessRecord("2026-10-12", 26.0, 30, 2.0),
            "expected_error": "Sleep must be between 0 and 24 hours",
        },
        {
            "description": "Negative activity minutes",
            "record": WellnessRecord("2026-10-12", 7.0, -15, 2.0),
            "expected_error": "Activity must be between 0 and 1440 minutes",
        },
        {
            "description": "Zero or negative water litres",
            "record": WellnessRecord("2026-10-12", 7.0, 30, -0.5),
            "expected_error": "Water must be positive",
        },
        {
            "description": "Invalid date format",
            "record": WellnessRecord("12-10-2026", 7.0, 30, 2.0),
            "expected_error": "Invalid date format",
        },
        {
            "description": "Empty date",
            "record": WellnessRecord("", 7.0, 30, 2.0),
            "expected_error": "Date is missing or empty",
        },
        {
            "description": "Out-of-range mood rating (>5)",
            "record": WellnessRecord("2026-10-12", 7.0, 30, 2.0, mood_rating=7),
            "expected_error": "mood_rating must be between 1 and 5",
        },
        {
            "description": "Out-of-range stress level (<1)",
            "record": WellnessRecord("2026-10-12", 7.0, 30, 2.0, stress_level=0),
            "expected_error": "stress_level must be between 1 and 5",
        },
    ]

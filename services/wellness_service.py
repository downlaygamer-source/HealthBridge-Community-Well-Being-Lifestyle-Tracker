"""
wellness_service.py — Service layer connecting database records to OOP analysis modules.

Integrates:
    - models.user.User
    - models.wellness_record.WellnessRecord
    - analysis.scoring.WellnessScorer & ScoringConfig
    - analysis.trends.TrendDetector & TrendConfig
    - analysis.recommendations.RecommendationEngine
"""

from __future__ import annotations
import sqlite3
from typing import Any
from models.user import User
from models.wellness_record import WellnessRecord
from analysis.scoring import WellnessScorer, ScoringConfig
from analysis.trends import TrendDetector
from analysis.recommendations import RecommendationEngine


def load_user_oop(conn: sqlite3.Connection, user_id: int) -> tuple[User, ScoringConfig]:
    """Load a User and their WellnessRecords from SQLite into OOP domain objects."""
    user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user_row:
        raise ValueError(f"User with ID {user_id} not found.")

    oop_user = User(name=user_row["full_name"], user_id=user_row["user_id"])

    # Load scoring configuration
    scoring_config = ScoringConfig(
        sleep_target=float(user_row["sleep_target"]),
        activity_target=int(user_row["activity_target"]),
        water_target=float(user_row["water_target"]),
        weight_sleep=float(user_row["weight_sleep"]),
        weight_activity=float(user_row["weight_activity"]),
        weight_water=float(user_row["weight_water"]),
    )

    # Fetch chronologically sorted records
    records_cursor = conn.execute(
        """
        SELECT record_date, sleep_hours, activity_minutes, water_litres, mood_rating, stress_level, notes
        FROM wellness_records
        WHERE user_id = ?
        ORDER BY record_date ASC
        """,
        (user_id,),
    )

    for r in records_cursor.fetchall():
        record = WellnessRecord(
            date=r["record_date"],
            sleep_hours=float(r["sleep_hours"]),
            activity_minutes=int(r["activity_minutes"]),
            water_litres=float(r["water_litres"]),
            mood_rating=int(r["mood_rating"]) if r["mood_rating"] is not None else None,
            stress_level=int(r["stress_level"]) if r["stress_level"] is not None else None,
        )
        oop_user.add_record(record)

    return oop_user, scoring_config


def compute_dashboard_metrics(conn: sqlite3.Connection, user_id: int) -> dict[str, Any]:
    """Compute comprehensive dashboard KPIs, trends, recommendations, and chart series."""
    user, scoring_config = load_user_oop(conn, user_id)
    scorer = WellnessScorer(scoring_config)
    trend_detector = TrendDetector()
    recommender = RecommendationEngine(scoring_config)

    records = user.records
    total_records = len(records)

    if total_records == 0:
        return {
            "total_records": 0,
            "latest_record": None,
            "overall_score": 0.0,
            "score_band": "No Data",
            "score_class": "info",
            "score_breakdown": {
                "sleep_pts": 0.0,
                "activity_pts": 0.0,
                "water_pts": 0.0,
                "mood_bonus": 0.0,
                "stress_penalty": 0.0,
            },
            "averages": {"sleep": 0, "activity": 0, "water": 0, "mood": 0, "stress": 0},
            "trends": {},
            "recommendations": [],
            "wow_changes": {},
            "chart_data": {"labels": [], "sleep": [], "activity": [], "water": [], "scores": [], "ma_scores": []},
            "scoring_config": scoring_config,
        }

    latest_record = records[-1]
    score_val = scorer.score(latest_record)
    ind_scores = scorer.indicator_scores(latest_record)

    # Calculate points contributed by each indicator
    sleep_pts = round(ind_scores["sleep"] * scoring_config.weight_sleep, 1)
    act_pts = round(ind_scores["activity"] * scoring_config.weight_activity, 1)
    water_pts = round(ind_scores["water"] * scoring_config.weight_water, 1)
    mood_bonus = round((ind_scores.get("mood", 0) / 100) * scoring_config.mood_bonus_max, 1) if "mood" in ind_scores else 0.0
    stress_penalty = round(((100 - ind_scores.get("stress", 100)) / 100) * scoring_config.stress_penalty_max, 1) if "stress" in ind_scores else 0.0

    # Calculate period averages over the last 7 records
    recent_window = records[-7:] if total_records >= 7 else records
    avgs_raw = scorer.indicator_averages(recent_window)
    avg_sleep = avgs_raw.get("sleep_hours", 0.0)
    avg_activity = avgs_raw.get("activity_minutes", 0.0)
    avg_water = avgs_raw.get("water_litres", 0.0)
    avg_mood = avgs_raw.get("mood_rating", 0.0)
    avg_stress = avgs_raw.get("stress_level", 0.0)

    # Moving averages of composite scores (3-day window)
    moving_avg_scores = scorer.moving_average(records, window=3)

    # Week-over-week changes
    prev_window = records[-14:-7] if total_records >= 14 else []
    wow = scorer.week_over_week_change(recent_window, prev_window)

    # Indicator-specific week-over-week changes
    wow_indicators: dict[str, float] = {}
    if prev_window:
        prev_avgs = scorer.indicator_averages(prev_window)
        for k in ["sleep_hours", "activity_minutes", "water_litres"]:
            p = prev_avgs.get(k, 0.0)
            c = avgs_raw.get(k, 0.0)
            diff = c - p
            pct = round((diff / p * 100), 1) if p else 0.0
            wow_indicators[k] = pct
    else:
        wow_indicators = {"sleep_hours": 0.0, "activity_minutes": 0.0, "water_litres": 0.0}

    # Detect trends
    raw_trends = trend_detector.detect_all(records)
    formatted_trends: dict[str, dict[str, Any]] = {}
    for ind, tdata in raw_trends.items():
        formatted_trends[ind] = {
            "trend": tdata.get("trend", "stable"),
            "classification": tdata.get("trend", "stable"),
            "percentage_change": tdata.get("change_pct", 0.0),
            "change_pct": tdata.get("change_pct", 0.0),
            "reason": TrendDetector.trend_description(tdata.get("trend", "")),
            "description": TrendDetector.trend_description(tdata.get("trend", "")),
            "recent_avg": tdata.get("recent_avg", 0.0),
            "previous_avg": tdata.get("previous_avg", 0.0),
        }

    # Generate recommendations
    recs_obj = recommender.generate(avgs_raw, raw_trends)
    recommendations = []
    for r in recs_obj:
        recommendations.append({
            "indicator": r.indicator,
            "priority": r.priority,
            "title": r.title,
            "suggestion": r.action_step,
            "action_step": r.action_step,
            "reason": r.reason,
            "target": r.target,
        })

    # Overall wellness score rating
    if score_val >= 80:
        score_band = "Optimal"
        score_class = "success"
    elif score_val >= 65:
        score_band = "Balanced"
        score_class = "primary"
    elif score_val >= 50:
        score_band = "Fair"
        score_class = "warning"
    else:
        score_band = "Needs Attention"
        score_class = "danger"

    # Chart datasets
    chart_labels = [r.date for r in records]
    chart_sleep = [r.sleep_hours for r in records]
    chart_activity = [r.activity_minutes for r in records]
    chart_water = [r.water_litres for r in records]
    chart_scores = [scorer.score(r) for r in records]

    # Align moving average list length with records length
    aligned_ma: list[float] = []
    w = 3
    for i in range(len(records)):
        sub = chart_scores[max(0, i - w + 1): i + 1]
        aligned_ma.append(round(sum(sub) / len(sub), 1))

    return {
        "total_records": total_records,
        "latest_record": latest_record,
        "overall_score": score_val,
        "score_band": score_band,
        "score_class": score_class,
        "score_breakdown": {
            "sleep_pts": sleep_pts,
            "activity_pts": act_pts,
            "water_pts": water_pts,
            "mood_bonus": mood_bonus,
            "stress_penalty": stress_penalty,
        },
        "averages": {
            "sleep": avg_sleep,
            "activity": avg_activity,
            "water": avg_water,
            "mood": avg_mood,
            "stress": avg_stress,
        },
        "trends": formatted_trends,
        "recommendations": recommendations,
        "wow_changes": wow_indicators,
        "chart_data": {
            "labels": chart_labels,
            "sleep": chart_sleep,
            "activity": chart_activity,
            "water": chart_water,
            "scores": chart_scores,
            "ma_scores": aligned_ma,
        },
        "scoring_config": scoring_config,
    }


def add_wellness_record_safe(
    conn: sqlite3.Connection,
    user_id: int,
    date: str,
    sleep_hours: float,
    activity_minutes: int,
    water_litres: float,
    mood_rating: int | None = None,
    stress_level: int | None = None,
    notes: str = "",
) -> tuple[bool, list[str]]:
    """Validate and insert a record via OOP domain model, then commit to SQLite."""
    user, _ = load_user_oop(conn, user_id)
    rec = WellnessRecord(
        date=date,
        sleep_hours=sleep_hours,
        activity_minutes=activity_minutes,
        water_litres=water_litres,
        mood_rating=mood_rating,
        stress_level=stress_level,
    )

    # Validate using the domain model
    success, messages = user.add_record(rec)
    if not success:
        return False, messages

    # Commit to SQLite
    try:
        conn.execute(
            """
            INSERT INTO wellness_records
            (user_id, record_date, sleep_hours, activity_minutes, water_litres, mood_rating, stress_level, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                date,
                sleep_hours,
                activity_minutes,
                water_litres,
                mood_rating,
                stress_level,
                notes,
            ),
        )
        conn.commit()
        return True, [f"Record successfully added for {date}."]
    except sqlite3.IntegrityError as e:
        return False, [f"Database constraint error: {str(e)}"]

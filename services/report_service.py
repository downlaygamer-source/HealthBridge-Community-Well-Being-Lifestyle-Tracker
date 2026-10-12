"""
report_service.py — Weekly report generation and export serialization service.
"""

from __future__ import annotations
import io
import csv
import json
import sqlite3
from typing import Any
from models.wellness_report import WellnessReport
from services.wellness_service import load_user_oop


def generate_user_weekly_report(
    conn: sqlite3.Connection,
    user_id: int,
    days: int = 7,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Generate weekly wellness report dictionary using OOP WellnessReport."""
    user, scoring_config = load_user_oop(conn, user_id)
    report = WellnessReport(user=user, scoring_config=scoring_config)
    data = report.generate_weekly_report(end_date=end_date, days=days)

    # Normalize keys for template compatibility
    records_list = data.get("records", [])
    data["daily_breakdown"] = [
        {
            "date": r.get("date"),
            "composite_score": r.get("score", 0.0) if r.get("score") is not None else 0.0,
            "indicators": {
                "sleep_hours": r.get("sleep_hours", 0.0) if r.get("sleep_hours") is not None else 0.0,
                "activity_minutes": r.get("activity_minutes", 0) if r.get("activity_minutes") is not None else 0,
                "water_litres": r.get("water_litres", 0.0) if r.get("water_litres") is not None else 0.0,
                "mood_rating": r.get("mood_rating"),
                "stress_level": r.get("stress_level"),
            },
        }
        for r in records_list
    ]

    # Ensure metadata keys exist
    data.setdefault("user", getattr(user, "name", "Community Member"))
    data.setdefault("user_id", getattr(user, "user_id", str(user_id)))
    data.setdefault("period", "No records logged" if not records_list else "Current 7-Day Window")
    data.setdefault("record_count", len(records_list))
    data.setdefault("disclaimer", data.get("note", ""))
    data.setdefault("trends", {})
    data.setdefault("recommendations", [])
    data.setdefault("has_data", bool(records_list))

    # Guarantee summary structure is always populated
    if "summary" not in data or not isinstance(data.get("summary"), dict):
        data["summary"] = {
            "average_score": 0.0,
            "week_over_week": {
                "composite_score": 0.0,
                "change_pct": 0.0,
                "change": 0.0,
                "current_avg": 0.0,
                "previous_avg": 0.0,
            },
            "indicator_averages": {
                "sleep_hours": 0.0,
                "activity_minutes": 0.0,
                "water_litres": 0.0,
                "mood_rating": 0.0,
                "stress_level": 0.0,
            },
            "moving_averages_3day": [],
        }
    else:
        summary = data["summary"]
        summary.setdefault("average_score", 0.0)
        wow = summary.setdefault("week_over_week", {})
        if "composite_score" not in wow:
            wow["composite_score"] = wow.get("change_pct", 0.0)
        ind_avgs = summary.setdefault("indicator_averages", {})
        for k in ("sleep_hours", "activity_minutes", "water_litres", "mood_rating", "stress_level"):
            ind_avgs.setdefault(k, 0.0)

    # Normalize trends
    for ind, tdata in data.get("trends", {}).items():
        tdata["percentage_change"] = tdata.get("change_pct", 0.0)
        tdata["classification"] = tdata.get("trend", "stable")
        tdata["reason"] = tdata.get("description", "")

    # Normalize recommendations
    for rec in data.get("recommendations", []):
        rec["suggestion"] = rec.get("action_step", "")

    return data


def export_report_json(report_data: dict[str, Any]) -> str:
    """Serialize report dictionary to formatted JSON string."""
    return json.dumps(report_data, indent=2)


def export_report_csv(report_data: dict[str, Any]) -> str:
    """Serialize daily breakdown and summary of report to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header metadata
    writer.writerow(["HealthBridge Weekly Wellness Report"])
    writer.writerow(["User", report_data.get("user", "")])
    writer.writerow(["Period", report_data.get("period", "")])
    writer.writerow(["Generated At", report_data.get("generated_at", "")])
    writer.writerow(["Disclaimer", report_data.get("disclaimer", "")])
    writer.writerow([])

    # Daily breakdown table
    writer.writerow([
        "Date",
        "Composite Score (0-100)",
        "Sleep Hours",
        "Activity Minutes",
        "Water Litres",
        "Mood Rating (1-5)",
        "Stress Level (1-5)",
    ])

    breakdown = report_data.get("daily_breakdown", [])
    if breakdown:
        for day in breakdown:
            ind = day.get("indicators", {})
            writer.writerow([
                day.get("date", ""),
                day.get("composite_score", ""),
                ind.get("sleep_hours", ""),
                ind.get("activity_minutes", ""),
                ind.get("water_litres", ""),
                ind.get("mood_rating", ""),
                ind.get("stress_level", ""),
            ])
    else:
        writer.writerow(["No records available for this period."])

    writer.writerow([])
    # Trends section
    writer.writerow(["Trend Analysis"])
    writer.writerow(["Indicator", "Classification", "Delta %", "Reason"])
    for ind, tdata in report_data.get("trends", {}).items():
        writer.writerow([
            ind,
            tdata.get("classification", ""),
            tdata.get("percentage_change", ""),
            tdata.get("reason", ""),
        ])

    writer.writerow([])
    # Recommendations section
    writer.writerow(["Non-Medical Recommendations"])
    writer.writerow(["Priority", "Indicator", "Suggestion", "Rationale"])
    for rec in report_data.get("recommendations", []):
        writer.writerow([
            rec.get("priority", ""),
            rec.get("indicator", ""),
            rec.get("suggestion", ""),
            rec.get("reason", ""),
        ])

    return output.getvalue()

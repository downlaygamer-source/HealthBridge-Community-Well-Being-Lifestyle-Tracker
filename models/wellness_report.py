"""
wellness_report.py — WellnessReport class.

Encapsulates the generation of weekly wellness summaries.
Composition: WellnessReport HAS-A User, HAS-A WellnessScorer, HAS-A TrendDetector,
HAS-A RecommendationEngine.

Separates reporting logic from raw data storage.
"""

from __future__ import annotations
from datetime import datetime
from models.user import User
from models.wellness_record import WellnessRecord
from analysis.scoring import WellnessScorer, ScoringConfig
from analysis.trends import TrendDetector, TrendConfig
from analysis.recommendations import RecommendationEngine, Recommendation
from utils.exporters import get_exporter


DISCLAIMER = (
    "NOTICE: HealthBridge is a non-diagnostic lifestyle tracker for educational "
    "and self-reflection purposes. It does NOT provide medical advice, diagnosis, "
    "or treatment. Consult a qualified healthcare professional for medical concerns."
)


class WellnessReport:
    """Generates comprehensive wellness reports for a single User.

    Demonstrates composition and separation of concerns:
    - User holds data
    - Scorer calculates normalized scores
    - TrendDetector analyses historical patterns
    - RecommendationEngine produces non-medical action steps
    """

    def __init__(
        self,
        user: User,
        scoring_config: ScoringConfig | None = None,
        trend_config: TrendConfig | None = None,
    ):
        self.user = user
        self.scorer = WellnessScorer(scoring_config)
        self.trend_detector = TrendDetector(trend_config)
        self.recommender = RecommendationEngine(scoring_config)

    # ------------------------------------------------------------------
    # Weekly Report Generation
    # ------------------------------------------------------------------
    def generate_weekly_report(
        self, end_date: str | None = None, days: int = 7
    ) -> dict:
        """Build a weekly wellness report covering the last *days* records.

        If *end_date* is not provided, uses the user's latest recorded date.
        Compares the current week against the preceding week (if available).
        """
        all_records = self.user.records
        empty_summary = {
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

        if not all_records:
            return {
                "user": self.user.name,
                "user_id": self.user.user_id,
                "period": "No records logged",
                "record_count": 0,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "disclaimer": DISCLAIMER,
                "note": DISCLAIMER,
                "error": "No records available for this user.",
                "has_data": False,
                "summary": empty_summary,
                "trends": {},
                "recommendations": [],
                "records": [],
            }

        # Filter records up to end_date
        if end_date:
            eligible = [r for r in all_records if r.date <= end_date]
        else:
            eligible = all_records

        if not eligible:
            return {
                "user": self.user.name,
                "user_id": self.user.user_id,
                "period": f"No records up to {end_date}",
                "record_count": 0,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "disclaimer": DISCLAIMER,
                "note": DISCLAIMER,
                "error": f"No records found up to {end_date}.",
                "has_data": False,
                "summary": empty_summary,
                "trends": {},
                "recommendations": [],
                "records": [],
            }

        # Current period (last `days` records)
        current_period = eligible[-days:]
        # Previous period (preceding `days` records, if available)
        prev_start = max(0, len(eligible) - (days * 2))
        prev_end = len(eligible) - days
        previous_period = eligible[prev_start:prev_end] if prev_end > 0 else []

        # 1. Indicator averages
        current_avgs = self.scorer.indicator_averages(current_period)
        for k in ("sleep_hours", "activity_minutes", "water_litres", "mood_rating", "stress_level"):
            current_avgs.setdefault(k, 0.0)

        # 2. Score breakdown per day
        daily_breakdowns = []
        for r in current_period:
            ind_scores = self.scorer.indicator_scores(r)
            composite = self.scorer.score(r)
            daily_breakdowns.append({
                "date": r.date,
                "composite_score": composite,
                "indicators": {
                    "sleep_hours": r.sleep_hours,
                    "activity_minutes": r.activity_minutes,
                    "water_litres": r.water_litres,
                    "mood_rating": r.mood_rating,
                    "stress_level": r.stress_level,
                },
                "normalised_scores": ind_scores,
            })

        # 3. Period scores & week-over-week
        current_avg_score = self.scorer.period_average(current_period)
        wow = self.scorer.week_over_week_change(current_period, previous_period)
        if "composite_score" not in wow:
            wow["composite_score"] = wow.get("change_pct", 0.0)

        # 4. Moving averages (3-day window)
        moving_avgs = self.scorer.moving_average(current_period, window=3)

        # 5. Trend analysis (run over a slightly wider history if available)
        history_for_trends = eligible[-(days * 2):] if len(eligible) >= days * 2 else eligible
        trends = self.trend_detector.detect_all(history_for_trends)

        # 6. Recommendations
        recs = self.recommender.generate(current_avgs, trends)

        # Date range string
        period_str = f"{current_period[0].date} to {current_period[-1].date}"

        report_data = {
            "user": self.user.name,
            "user_id": self.user.user_id,
            "period": period_str,
            "record_count": len(current_period),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "disclaimer": DISCLAIMER,
            "has_data": True,
            "summary": {
                "average_score": current_avg_score,
                "week_over_week": wow,
                "indicator_averages": current_avgs,
                "moving_averages_3day": moving_avgs,
            },
            "trends": {
                ind: {
                    "trend": t.get("trend"),
                    "description": TrendDetector.trend_description(t.get("trend", "")),
                    "emoji": TrendDetector.trend_emoji(t.get("trend", "")),
                    "change_pct": t.get("change_pct"),
                    "recent_avg": t.get("recent_avg"),
                    "previous_avg": t.get("previous_avg"),
                    "sudden_changes": t.get("sudden_changes", []),
                }
                for ind, t in trends.items()
            },
            "recommendations": [r.to_dict() for r in recs],
            "records": [
                {
                    "date": b["date"],
                    "score": b["composite_score"],
                    **b["indicators"],
                }
                for b in daily_breakdowns
            ],
        }

        return report_data

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------
    def export(
        self,
        fmt: str = "json",
        output_dir: str = ".",
        filename: str | None = None,
        days: int = 7,
    ) -> str:
        """Generate and export the weekly report.

        Returns the path of the created file.
        """
        report_data = self.generate_weekly_report(days=days)
        exporter = get_exporter(fmt, output_dir=output_dir)

        if not filename:
            safe_name = self.user.user_id
            filename = f"healthbridge_report_{safe_name}.{fmt}"

        return exporter.export(report_data, filename)

    # ------------------------------------------------------------------
    # Formatted Console Display
    # ------------------------------------------------------------------
    def print_weekly_report(self, days: int = 7) -> None:
        """Print an eye-catching, formatted text report to stdout."""
        data = self.generate_weekly_report(days=days)

        if "error" in data:
            print(f"\n❌ Error for {self.user.name}: {data['error']}\n")
            return

        w = 64
        sep = "═" * w
        thin_sep = "─" * w

        print(f"\n{sep}")
        print(f"  HEALTHBRIDGE WEEKLY WELLNESS REPORT".center(w))
        print(f"  SDG 3: Good Health & Well-Being  |  SDG 10: Reduced Inequalities".center(w))
        print(f"{sep}")
        print(f"  User:   {data['user']} (ID: {data['user_id']})")
        print(f"  Period: {data['period']} ({data['record_count']} records)")
        print(f"  Date:   {data['generated_at']}")
        print(f"{thin_sep}")

        # Overall Score & WoW
        s = data["summary"]
        avg_score = s["average_score"]
        wow = s["week_over_week"]
        change_sign = "+" if wow["change"] > 0 else ""
        wow_str = (
            f"{change_sign}{wow['change']} pts ({change_sign}{wow['change_pct']}%)"
            if wow["previous_avg"] > 0
            else "First week of tracking"
        )
        print(f"\n  OVERALL WELLNESS SCORE:  {avg_score} / 100")
        print(f"  Week-over-Week Change:   {wow_str}")

        # Indicator Averages
        print(f"\n  {thin_sep}")
        print(f"  INDICATOR AVERAGES (Target comparison)")
        print(f"  {thin_sep}")
        avgs = s["indicator_averages"]
        targets = {
            "sleep_hours": (self.scorer.config.sleep_target, "hours"),
            "activity_minutes": (self.scorer.config.activity_target, "min"),
            "water_litres": (self.scorer.config.water_target, "L"),
            "mood_rating": (self.scorer.config.mood_target, "/5"),
            "stress_level": (self.scorer.config.stress_target, "/5"),
        }
        for ind, (target, unit) in targets.items():
            if ind in avgs:
                val = avgs[ind]
                status = "✅" if (val >= target if ind != "stress_level" else val <= target) else "⚠️"
                print(f"  {status} {ind.replace('_', ' ').title():<20} {val} {unit:<5} (Target: {target} {unit})")

        # Trends
        print(f"\n  {thin_sep}")
        print(f"  DETECTED TRENDS (Rule-based sliding window)")
        print(f"  {thin_sep}")
        for ind, t in data["trends"].items():
            name = ind.replace("_", " ").title()
            print(f"  {t['emoji']}  {name:<20} {t['description']} ({t['change_pct']:+0.1f}%)")
            for alert in t.get("sudden_changes", []):
                direction = "jump" if alert["direction"] == "sudden_increase" else "drop"
                print(f"      ⚡ Alert: Sudden {direction} of {alert['change']} on day {alert['day_index']}")

        # Recommendations
        print(f"\n  {thin_sep}")
        print(f"  PERSONALIZED RECOMMENDATIONS (Non-medical)")
        print(f"  {thin_sep}")
        recs = data.get("recommendations", [])
        if not recs:
            print("  🌟 All indicators are meeting target! Keep up the great routine.")
        else:
            for r in recs:
                badge = "🔴 High" if r["priority"] == 1 else "🟡 Medium" if r["priority"] == 2 else "🔵 Low"
                print(f"\n  [{badge}] {r['title']} (Target: {r['target']})")
                print(f"    Why:    {r['reason']}")
                print(f"    Action: {r['action_step']}")

        # Disclaimer
        print(f"\n  {thin_sep}")
        print(f"  ⚠️  {data['disclaimer']}")
        print(f"{sep}\n")

"""
recommendations.py — Non-medical lifestyle suggestion engine.

Demonstrates polymorphism:
    BaseRecommendationStrategy (abstract)
        ├── SleepRecommendation
        ├── ActivityRecommendation
        ├── HydrationRecommendation
        ├── MoodRecommendation
        └── StressRecommendation

Identifies priority areas by looking at:
    1. Distance from target
    2. Trend direction (declining indicators get higher priority)
    3. Missing data frequency

Outputs structured suggestions with a clear **reason** and a practical,
non-medical **action step**.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from models.wellness_record import WellnessRecord
from analysis.scoring import ScoringConfig


@dataclass
class Recommendation:
    """A single non-medical suggestion for the user."""

    indicator: str
    priority: int           # 1 (highest) to 5 (lowest)
    title: str
    reason: str
    action_step: str
    target: str

    def to_dict(self) -> dict:
        return {
            "indicator": self.indicator,
            "priority": self.priority,
            "title": self.title,
            "reason": self.reason,
            "action_step": self.action_step,
            "target": self.target,
        }

    def __str__(self) -> str:
        return (
            f"[Priority {self.priority}] {self.title}\n"
            f"   Why: {self.reason}\n"
            f"   Action: {self.action_step}\n"
            f"   Target: {self.target}"
        )


# ---------------------------------------------------------------------------
# Strategy interface & implementations (polymorphism)
# ---------------------------------------------------------------------------
class BaseRecommendationStrategy(ABC):
    """Abstract base strategy for generating recommendations for an indicator."""

    @abstractmethod
    def evaluate(
        self,
        recent_avg: float,
        target: float,
        trend: str,
        config: ScoringConfig,
    ) -> Recommendation | None:
        """Evaluate the indicator and return a :class:`Recommendation` or None."""


class SleepRecommendation(BaseRecommendationStrategy):
    """Generates practical sleep hygiene tips."""

    def evaluate(
        self, recent_avg: float, target: float, trend: str, config: ScoringConfig
    ) -> Recommendation | None:
        if recent_avg >= target and trend != "declining":
            return None

        priority = 1 if recent_avg < target * 0.75 or trend == "declining" else 2

        if recent_avg < 6:
            reason = (
                f"Recent sleep ({recent_avg:.1f}h) is significantly below the "
                f"{target:.0f}h target, which can reduce daily energy and focus."
            )
            action = "Try setting a wind-down alarm 45 minutes before bedtime; avoid screens in that window."
        elif trend == "declining":
            reason = (
                f"Sleep has been trending downward recently (average {recent_avg:.1f}h)."
            )
            action = "Keep a consistent sleep schedule this week — go to bed and wake up at the same time each day."
        else:
            reason = f"Average sleep ({recent_avg:.1f}h) is slightly below the {target:.0f}h target."
            action = "Aim for 30 minutes more sleep by shifting your bedtime earlier."

        return Recommendation(
            indicator="sleep",
            priority=priority,
            title="Consistent Sleep Routine",
            reason=reason,
            action_step=action,
            target=f"{target:.0f} hours per night",
        )


class ActivityRecommendation(BaseRecommendationStrategy):
    """Generates physical activity suggestions."""

    def evaluate(
        self, recent_avg: float, target: float, trend: str, config: ScoringConfig
    ) -> Recommendation | None:
        if recent_avg >= target and trend != "declining":
            return None

        priority = 1 if recent_avg < target * 0.5 or trend == "declining" else 2

        if recent_avg < 15:
            reason = (
                f"Daily activity ({recent_avg:.0f} min) is well below the "
                f"{target:.0f} min target. Even small amounts of movement help."
            )
            action = "Start with a 10-minute walk after lunch or dinner; take short movement breaks every hour."
        elif trend == "declining":
            reason = (
                f"Physical activity has been dropping (recent average: {recent_avg:.0f} min/day)."
            )
            action = "Schedule your movement time like an appointment; pair it with an enjoyable podcast or music."
        else:
            reason = f"Activity ({recent_avg:.0f} min) is just below your {target:.0f} min goal."
            action = "Add a 15-minute brisk walk or stretching routine to reach your daily goal."

        return Recommendation(
            indicator="activity",
            priority=priority,
            title="Increase Daily Movement",
            reason=reason,
            action_step=action,
            target=f"{target:.0f} minutes per day",
        )


class HydrationRecommendation(BaseRecommendationStrategy):
    """Generates hydration suggestions."""

    def evaluate(
        self, recent_avg: float, target: float, trend: str, config: ScoringConfig
    ) -> Recommendation | None:
        if recent_avg >= target and trend != "declining":
            return None

        priority = 2 if recent_avg < target * 0.6 else 3

        if recent_avg < 1.0:
            reason = (
                f"Water intake ({recent_avg:.2f}L) is less than half the "
                f"{target:.1f}L target. Dehydration can affect energy and concentration."
            )
            action = "Keep a water bottle on your desk; try finishing one glass before your morning coffee."
        else:
            reason = f"Hydration ({recent_avg:.2f}L) is below the recommended {target:.1f}L."
            action = "Set hourly drink reminders or have a glass of water with each meal."

        return Recommendation(
            indicator="water",
            priority=priority,
            title="Boost Hydration",
            reason=reason,
            action_step=action,
            target=f"{target:.1f} litres per day",
        )


class MoodRecommendation(BaseRecommendationStrategy):
    """Generates suggestions when mood is tracking low."""

    def evaluate(
        self, recent_avg: float, target: float, trend: str, config: ScoringConfig
    ) -> Recommendation | None:
        if recent_avg >= target and trend != "declining":
            return None

        return Recommendation(
            indicator="mood",
            priority=3,
            title="Mindfulness & Social Connection",
            reason=f"Mood ratings have averaged {recent_avg:.1f}/5 recently.",
            action_step="Dedicate 10 minutes to an activity you enjoy (reading, music, talking to a friend).",
            target=f"{target:.0f}/5 rating",
        )


class StressRecommendation(BaseRecommendationStrategy):
    """Generates stress management suggestions (lower stress is better)."""

    def evaluate(
        self, recent_avg: float, target: float, trend: str, config: ScoringConfig
    ) -> Recommendation | None:
        # For stress, values ABOVE target indicate high stress
        if recent_avg <= target and trend != "declining":  # declining here = worsening
            return None

        priority = 1 if recent_avg >= 4 else 2
        return Recommendation(
            indicator="stress",
            priority=priority,
            title="Stress Reduction Breaks",
            reason=f"Stress has been elevated ({recent_avg:.1f}/5; ideal is ≤ {target:.0f}).",
            action_step="Try 5 minutes of box breathing (4s in, 4s hold, 4s out, 4s hold) during busy periods.",
            target=f"≤ {target:.0f}/5 rating",
        )


# ---------------------------------------------------------------------------
# Recommendation Engine (orchestrates strategies)
# ---------------------------------------------------------------------------
class RecommendationEngine:
    """Evaluates all indicators and returns a prioritised list of suggestions.

    Uses a dictionary of polymorphic strategies to decouple indicator logic.
    """

    def __init__(self, config: ScoringConfig | None = None):
        self.config = config or ScoringConfig()
        self._strategies: dict[str, BaseRecommendationStrategy] = {
            "sleep_hours":      SleepRecommendation(),
            "activity_minutes": ActivityRecommendation(),
            "water_litres":     HydrationRecommendation(),
            "mood_rating":      MoodRecommendation(),
            "stress_level":     StressRecommendation(),
        }

    def generate(
        self,
        indicator_averages: dict[str, float],
        trends: dict[str, dict],
    ) -> list[Recommendation]:
        """Produce prioritised recommendations based on averages and trends.

        Returns a list of :class:`Recommendation` objects sorted by priority
        (1 = highest priority).
        """
        targets = {
            "sleep_hours":      self.config.sleep_target,
            "activity_minutes": float(self.config.activity_target),
            "water_litres":     self.config.water_target,
            "mood_rating":      float(self.config.mood_target),
            "stress_level":     float(self.config.stress_target),
        }

        recs: list[Recommendation] = []

        for field_name, strategy in self._strategies.items():
            avg = indicator_averages.get(field_name)
            if avg is None:
                continue

            target = targets.get(field_name, 1.0)
            trend_info = trends.get(field_name, {})
            trend = trend_info.get("trend", "stable")

            rec = strategy.evaluate(avg, target, trend, self.config)
            if rec:
                recs.append(rec)

        # Sort by priority ascending (1 first), then indicator name
        recs.sort(key=lambda r: (r.priority, r.indicator))
        return recs

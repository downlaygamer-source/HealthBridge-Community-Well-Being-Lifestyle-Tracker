"""
scoring.py — Configurable weighted wellness score calculator.

Default indicator weights:
    sleep_hours       40 %
    activity_minutes  35 %
    hydration         25 %

Mood and stress are bonus adjustments when provided.

Each indicator is normalised to 0–100 relative to a configurable target
(capped at 100 %).  The overall score is the weighted sum.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from statistics import mean
from models.wellness_record import WellnessRecord


@dataclass
class ScoringConfig:
    """Holds targets and weights used by the scorer.

    Adjust these to change what "100 %" means for each indicator.
    """

    # Targets — "ideal" daily values
    sleep_target: float = 8.0          # hours
    activity_target: int = 30          # minutes
    water_target: float = 2.0          # litres
    mood_target: int = 4               # 1-5 scale
    stress_target: int = 2             # 1-5 scale (lower is better)

    # Weights for the three core indicators (must sum to 1.0)
    weight_sleep: float = 0.40
    weight_activity: float = 0.35
    weight_water: float = 0.25

    # Bonus adjustments for optional indicators
    mood_bonus_max: float = 5.0        # max points added
    stress_penalty_max: float = 5.0    # max points subtracted

    def __post_init__(self):
        total = self.weight_sleep + self.weight_activity + self.weight_water
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Core weights must sum to 1.0; got {total:.3f}."
            )


class WellnessScorer:
    """Calculates normalised wellness scores from WellnessRecord objects.

    Composition: a scorer HAS-A ScoringConfig.
    """

    def __init__(self, config: ScoringConfig | None = None):
        self.config = config or ScoringConfig()

    # ------------------------------------------------------------------
    # Per-indicator normalisation (0–100)
    # ------------------------------------------------------------------
    def _normalise(self, value: float, target: float, *, invert: bool = False) -> float:
        """Normalise *value* to 0–100 relative to *target*, capped at 100.

        When *invert* is True, lower values score higher (used for stress).
        """
        if target == 0:
            return 100.0
        if invert:
            # stress_level: 1 is best (100), target (e.g. 2) is "acceptable"
            # 5 is worst (0).  Linear scale from 1 → 100  to  5 → 0.
            return max(0.0, min(100.0, (5 - value) / (5 - 1) * 100))
        return min(value / target, 1.0) * 100

    def indicator_scores(self, record: WellnessRecord) -> dict[str, float]:
        """Return individual normalised scores for each indicator."""
        cfg = self.config
        scores: dict[str, float] = {
            "sleep":    round(self._normalise(record.sleep_hours, cfg.sleep_target), 1),
            "activity": round(self._normalise(record.activity_minutes, cfg.activity_target), 1),
            "water":    round(self._normalise(record.water_litres, cfg.water_target), 1),
        }
        if record.mood_rating is not None:
            scores["mood"] = round(self._normalise(record.mood_rating, cfg.mood_target), 1)
        if record.stress_level is not None:
            scores["stress"] = round(
                self._normalise(record.stress_level, cfg.stress_target, invert=True), 1
            )
        return scores

    # ------------------------------------------------------------------
    # Composite score
    # ------------------------------------------------------------------
    def score(self, record: WellnessRecord) -> float:
        """Compute the weighted wellness score (0–100) for a single record."""
        ind = self.indicator_scores(record)
        cfg = self.config

        composite = (
            ind["sleep"]    * cfg.weight_sleep
            + ind["activity"] * cfg.weight_activity
            + ind["water"]    * cfg.weight_water
        )

        # Optional bonus / penalty
        if "mood" in ind:
            composite += (ind["mood"] / 100) * cfg.mood_bonus_max
        if "stress" in ind:
            composite -= ((100 - ind["stress"]) / 100) * cfg.stress_penalty_max

        return round(max(0, min(composite, 105)), 1)  # cap at 105 with bonuses

    # ------------------------------------------------------------------
    # Aggregations
    # ------------------------------------------------------------------
    def moving_average(self, records: list[WellnessRecord], window: int = 3) -> list[float]:
        """Return a list of moving-average scores over *window* records."""
        scores = [self.score(r) for r in records]
        if len(scores) < window:
            return [round(mean(scores), 1)] if scores else []
        return [
            round(mean(scores[i:i + window]), 1)
            for i in range(len(scores) - window + 1)
        ]

    def period_average(self, records: list[WellnessRecord]) -> float:
        """Average score across all supplied records."""
        if not records:
            return 0.0
        return round(mean(self.score(r) for r in records), 1)

    def week_over_week_change(
        self, current_week: list[WellnessRecord], previous_week: list[WellnessRecord]
    ) -> dict[str, float]:
        """Return the absolute and percentage change between two weeks.

        Returns dict with keys ``current_avg``, ``previous_avg``,
        ``change``, ``change_pct``.
        """
        cur = self.period_average(current_week)
        prev = self.period_average(previous_week)
        change = round(cur - prev, 1)
        pct = round((change / prev) * 100, 1) if prev else 0.0
        return {
            "current_avg": cur,
            "previous_avg": prev,
            "change": change,
            "change_pct": pct,
        }

    def indicator_averages(self, records: list[WellnessRecord]) -> dict[str, float]:
        """Average raw value for each indicator across *records*."""
        if not records:
            return {}
        avgs: dict[str, float] = {
            "sleep_hours":      round(mean(r.sleep_hours for r in records), 1),
            "activity_minutes": round(mean(r.activity_minutes for r in records), 1),
            "water_litres":     round(mean(r.water_litres for r in records), 2),
        }
        moods = [r.mood_rating for r in records if r.mood_rating is not None]
        if moods:
            avgs["mood_rating"] = round(mean(moods), 1)
        stress = [r.stress_level for r in records if r.stress_level is not None]
        if stress:
            avgs["stress_level"] = round(mean(stress), 1)
        return avgs

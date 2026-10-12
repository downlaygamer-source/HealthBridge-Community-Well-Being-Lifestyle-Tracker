"""
trends.py — Rule-based trend detection for wellness indicators.

Compares a recent window of records against a previous window to detect:
    • Sustained improvement  (recent average > previous by > 10 %)
    • Sustained decline      (recent average < previous by > 10 %)
    • Stagnation             (change within ±5 %)
    • Sudden change          (single-day jump/drop > 25 % of target)

All thresholds are transparent and configurable.
"""

from __future__ import annotations
from dataclasses import dataclass
from statistics import mean
from models.wellness_record import WellnessRecord


# ---------------------------------------------------------------------------
# Trend labels
# ---------------------------------------------------------------------------
IMPROVING  = "improving"
DECLINING  = "declining"
STAGNANT   = "stagnant"
SUDDEN_UP  = "sudden_increase"
SUDDEN_DOWN = "sudden_decrease"
STABLE     = "stable"
INSUFFICIENT = "insufficient_data"


@dataclass
class TrendConfig:
    """Thresholds controlling trend classification."""

    improvement_pct: float = 10.0   # % above which we call "improving"
    decline_pct: float = 10.0       # % below which we call "declining"
    stagnation_pct: float = 5.0     # within ±% is "stagnant"
    sudden_change_pct: float = 25.0 # single-day jump threshold
    window_size: int = 3            # number of days in each comparison window


class TrendDetector:
    """Detects trends across a sequence of wellness records.

    Uses a simple sliding-window comparison with configurable thresholds.
    """

    def __init__(self, config: TrendConfig | None = None):
        self.config = config or TrendConfig()

    # ------------------------------------------------------------------
    # Per-indicator helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _extract(records: list[WellnessRecord], indicator: str) -> list[float]:
        """Pull a flat list of values for *indicator* from *records*."""
        values: list[float] = []
        for r in records:
            val = getattr(r, indicator, None)
            if val is not None:
                values.append(float(val))
        return values

    def _window_trend(self, recent: list[float], previous: list[float]) -> str:
        """Compare two value windows and return a trend label."""
        if not recent or not previous:
            return INSUFFICIENT

        avg_recent = mean(recent)
        avg_prev = mean(previous)

        if avg_prev == 0:
            return STABLE

        change_pct = ((avg_recent - avg_prev) / abs(avg_prev)) * 100

        if change_pct > self.config.improvement_pct:
            return IMPROVING
        if change_pct < -self.config.decline_pct:
            return DECLINING
        if abs(change_pct) <= self.config.stagnation_pct:
            return STAGNANT
        return STABLE

    def _detect_sudden(self, values: list[float], target: float) -> list[dict]:
        """Identify single-day jumps that exceed the sudden-change threshold."""
        alerts: list[dict] = []
        threshold = target * (self.config.sudden_change_pct / 100)
        for i in range(1, len(values)):
            diff = values[i] - values[i - 1]
            if abs(diff) >= threshold:
                alerts.append({
                    "day_index": i,
                    "change": round(diff, 2),
                    "direction": SUDDEN_UP if diff > 0 else SUDDEN_DOWN,
                })
        return alerts

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    INDICATOR_TARGETS = {
        "sleep_hours": 8.0,
        "activity_minutes": 30.0,
        "water_litres": 2.0,
        "mood_rating": 4.0,
        "stress_level": 2.0,
    }

    def detect(
        self, records: list[WellnessRecord], indicator: str
    ) -> dict:
        """Analyse trend for a single indicator across *records*.

        Returns a dict with keys ``trend``, ``recent_avg``, ``previous_avg``,
        ``change_pct``, and ``sudden_changes``.
        """
        w = self.config.window_size
        values = self._extract(records, indicator)

        if len(values) < w * 2:
            return {"trend": INSUFFICIENT, "detail": "Need at least 2× window records."}

        previous_window = values[-(w * 2):-w]
        recent_window = values[-w:]

        trend = self._window_trend(recent_window, previous_window)

        avg_recent = round(mean(recent_window), 2)
        avg_prev = round(mean(previous_window), 2)
        change_pct = round(((avg_recent - avg_prev) / abs(avg_prev)) * 100, 1) if avg_prev else 0

        target = self.INDICATOR_TARGETS.get(indicator, 1.0)
        sudden = self._detect_sudden(values, target)

        return {
            "indicator": indicator,
            "trend": trend,
            "recent_avg": avg_recent,
            "previous_avg": avg_prev,
            "change_pct": change_pct,
            "sudden_changes": sudden,
        }

    def detect_all(self, records: list[WellnessRecord]) -> dict[str, dict]:
        """Run trend detection on every indicator and return results keyed by name."""
        indicators = ["sleep_hours", "activity_minutes", "water_litres",
                       "mood_rating", "stress_level"]
        results: dict[str, dict] = {}
        for ind in indicators:
            values = self._extract(records, ind)
            if values:  # skip indicators with no data
                results[ind] = self.detect(records, ind)
        return results

    # ------------------------------------------------------------------
    # Human-readable summary
    # ------------------------------------------------------------------
    @staticmethod
    def trend_emoji(trend: str) -> str:
        """Return a unicode symbol for the trend direction."""
        return {
            IMPROVING: "📈",
            DECLINING: "📉",
            STAGNANT: "➡️",
            SUDDEN_UP: "⚡↑",
            SUDDEN_DOWN: "⚡↓",
            STABLE: "✅",
            INSUFFICIENT: "❓",
        }.get(trend, "")

    @staticmethod
    def trend_description(trend: str) -> str:
        """Return a plain-English label for a trend."""
        return {
            IMPROVING: "Sustained improvement",
            DECLINING: "Sustained decline",
            STAGNANT: "Stagnant (little change)",
            SUDDEN_UP: "Sudden increase",
            SUDDEN_DOWN: "Sudden decrease",
            STABLE: "Stable",
            INSUFFICIENT: "Insufficient data",
        }.get(trend, "Unknown")

"""
wellness_record.py — WellnessRecord data model.

A single day's self-reported wellness indicators with built-in validation.
Uses :mod:`dataclasses` for concise construction and :mod:`utils.validators`
for rule-based input checks.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from utils.validators import validate_date, validate_range, validate_positive


@dataclass
class WellnessRecord:
    """One day of self-reported wellness data.

    Attributes:
        date:             ISO date string (YYYY-MM-DD).
        sleep_hours:      Hours of sleep (0–24).
        activity_minutes: Minutes of physical activity (≥0).
        water_litres:     Litres of water consumed (>0).
        mood_rating:      Subjective mood (1–5, optional).
        stress_level:     Subjective stress (1–5, optional; lower is better).
    """

    date: str
    sleep_hours: float
    activity_minutes: int
    water_litres: float
    mood_rating: int | None = None
    stress_level: int | None = None
    notes: str = ""

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate(self) -> list[str]:
        """Return a list of validation error strings (empty if valid)."""
        errors: list[str] = []

        # Date
        err = validate_date(self.date)
        if err:
            errors.append(err)

        # Core numeric fields
        for field_name, value in [
            ("sleep_hours", self.sleep_hours),
            ("activity_minutes", self.activity_minutes),
            ("water_litres", self.water_litres),
        ]:
            err = validate_range(field_name, value)
            if err:
                errors.append(err)

        # water must be positive
        if self.water_litres is not None:
            err = validate_positive("water_litres", self.water_litres)
            if err and err not in errors:
                errors.append(err)

        # Optional fields — validate only when provided
        if self.mood_rating is not None:
            err = validate_range("mood_rating", self.mood_rating)
            if err:
                errors.append(err)

        if self.stress_level is not None:
            err = validate_range("stress_level", self.stress_level)
            if err:
                errors.append(err)

        return errors

    def is_valid(self) -> bool:
        """Return True when all fields pass validation."""
        return len(self.validate()) == 0

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Return the record as a plain dictionary (for JSON/CSV export)."""
        return asdict(self)

    def __str__(self) -> str:
        parts = [
            f"Date: {self.date}",
            f"Sleep: {self.sleep_hours}h",
            f"Activity: {self.activity_minutes}min",
            f"Water: {self.water_litres}L",
        ]
        if self.mood_rating is not None:
            parts.append(f"Mood: {self.mood_rating}/5")
        if self.stress_level is not None:
            parts.append(f"Stress: {self.stress_level}/5")
        return " | ".join(parts)

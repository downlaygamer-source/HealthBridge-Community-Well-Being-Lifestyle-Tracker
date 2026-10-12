"""
validators.py — Data validation utilities for HealthBridge.

Provides reusable validation functions for wellness record fields.
Each validator returns None on success or a descriptive error string on failure.
"""

from datetime import datetime


# ---------------------------------------------------------------------------
# Indicator range definitions (min, max, unit label)
# ---------------------------------------------------------------------------
INDICATOR_RANGES = {
    "sleep_hours":      (0, 24,   "hours"),
    "activity_minutes": (0, 1440, "minutes"),
    "water_litres":     (0, 20,   "litres"),
    "mood_rating":      (1, 5,    "rating 1-5"),
    "stress_level":     (1, 5,    "rating 1-5"),
}


def validate_date(date_str: str) -> str | None:
    """Validate that *date_str* is a non-empty ISO-format date (YYYY-MM-DD)."""
    if not date_str or not date_str.strip():
        return "Date is missing or empty."
    try:
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        return f"Invalid date format '{date_str}'; expected YYYY-MM-DD."
    return None


def validate_range(field_name: str, value) -> str | None:
    """Validate that *value* falls within the accepted range for *field_name*.

    Returns None when valid, or a human-readable error message otherwise.
    """
    if value is None:
        return f"{field_name} is missing."

    spec = INDICATOR_RANGES.get(field_name)
    if spec is None:
        return f"Unknown indicator '{field_name}'."

    lo, hi, unit = spec
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return f"{field_name} must be a number, got '{value}'."

    if numeric < lo or numeric > hi:
        return f"{field_name} must be between {lo} and {hi} {unit}; got {numeric}."
    return None


def validate_positive(field_name: str, value) -> str | None:
    """Ensure *value* is strictly positive (> 0)."""
    try:
        if float(value) <= 0:
            return f"{field_name} must be positive; got {value}."
    except (TypeError, ValueError):
        return f"{field_name} must be a number; got '{value}'."
    return None


def validate_record_fields(data: dict) -> list[str]:
    """Run all field-level validations on a raw record dictionary.

    Returns a list of error strings (empty when everything is valid).
    """
    errors: list[str] = []

    # Date
    date_err = validate_date(data.get("date", ""))
    if date_err:
        errors.append(date_err)

    # Numeric indicators
    for field_name in INDICATOR_RANGES:
        val = data.get(field_name)
        if val is None:
            # mood_rating and stress_level are optional
            if field_name in ("mood_rating", "stress_level"):
                continue
            errors.append(f"{field_name} is missing.")
            continue
        range_err = validate_range(field_name, val)
        if range_err:
            errors.append(range_err)

    # water_litres must also be > 0
    water = data.get("water_litres")
    if water is not None:
        pos_err = validate_positive("water_litres", water)
        if pos_err:
            errors.append(pos_err)

    return errors

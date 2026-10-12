"""
user.py — User data model.

Each User owns a collection of :class:`WellnessRecord` objects.
Demonstrates composition (User HAS-A list of records) and encapsulation
(records are managed through :meth:`add_record`).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from models.wellness_record import WellnessRecord


@dataclass
class User:
    """A HealthBridge user who tracks daily wellness indicators.

    Attributes:
        name:    Display name (must be non-empty).
        user_id: Unique identifier string.
        records: Chronologically ordered list of validated WellnessRecords.
    """

    name: str
    user_id: str = ""
    records: list[WellnessRecord] = field(default_factory=list, repr=False)

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("User name must not be empty.")
        self.name = self.name.strip()
        if not self.user_id:
            # Auto-generate a simple id from the name
            self.user_id = self.name.lower().replace(" ", "_")

    # ------------------------------------------------------------------
    # Record management
    # ------------------------------------------------------------------
    def add_record(self, record: WellnessRecord) -> tuple[bool, list[str]]:
        """Validate and append a record.

        Returns:
            A tuple of (success: bool, messages: list[str]).
            On failure the messages list contains the validation errors.
        """
        # Validate fields
        errors = record.validate()
        if errors:
            return False, [f"REJECTED ({record.date}): {e}" for e in errors]

        # Check for duplicate date
        if any(r.date == record.date for r in self.records):
            return False, [f"REJECTED: Duplicate date '{record.date}' for {self.name}."]

        self.records.append(record)
        # Keep records sorted by date
        self.records.sort(key=lambda r: r.date)
        return True, [f"Added record for {self.name} on {record.date}."]

    def get_records_in_range(self, start_date: str, end_date: str) -> list[WellnessRecord]:
        """Return records whose date falls within [start_date, end_date]."""
        return [r for r in self.records if start_date <= r.date <= end_date]

    def get_latest_records(self, n: int = 7) -> list[WellnessRecord]:
        """Return the most recent *n* records (sorted oldest-first)."""
        return self.records[-n:]

    @property
    def record_count(self) -> int:
        """Number of stored records."""
        return len(self.records)

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        return f"User({self.name}, records={self.record_count})"

    def summary(self) -> str:
        """One-line summary of the user and their data span."""
        if not self.records:
            return f"{self.name}: no records yet."
        first = self.records[0].date
        last = self.records[-1].date
        return f"{self.name}: {self.record_count} records from {first} to {last}."

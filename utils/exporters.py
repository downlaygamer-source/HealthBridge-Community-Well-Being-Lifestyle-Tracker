"""
exporters.py — CSV and JSON export utilities for HealthBridge.

Demonstrates inheritance and polymorphism:
    BaseExporter (abstract) -> JSONExporter, CSVExporter

Each exporter serialises a report dictionary to a file and returns the path.
"""

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path


class BaseExporter(ABC):
    """Abstract base class for report exporters.

    Subclasses must implement :meth:`export`, which writes a report dictionary
    to a file and returns the absolute path of the written file.
    """

    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def export(self, report_data: dict, filename: str) -> str:
        """Write *report_data* to *filename* and return its path."""

    def _resolve(self, filename: str) -> Path:
        """Return full output path for *filename*."""
        return self.output_dir / filename

    def __repr__(self):
        return f"{self.__class__.__name__}(output_dir='{self.output_dir}')"


class JSONExporter(BaseExporter):
    """Export a report dictionary as a pretty-printed JSON file."""

    def export(self, report_data: dict, filename: str = "report.json") -> str:
        path = self._resolve(filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(report_data, fh, indent=2, ensure_ascii=False, default=str)
        return str(path)


class CSVExporter(BaseExporter):
    """Export the per-record rows of a report as a CSV file.

    Expects *report_data* to contain a ``"records"`` key whose value is a
    list of flat dictionaries.  Meta fields (user name, note, etc.) are
    written as a header comment.
    """

    def export(self, report_data: dict, filename: str = "report.csv") -> str:
        path = self._resolve(filename)
        records = report_data.get("records", [])
        if not records:
            # Write an empty CSV with just the meta
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(f"# User: {report_data.get('user', 'N/A')}\n")
                fh.write(f"# Note: {report_data.get('note', '')}\n")
            return str(path)

        fieldnames = list(records[0].keys())

        with open(path, "w", encoding="utf-8", newline="") as fh:
            # Meta header
            fh.write(f"# User: {report_data.get('user', 'N/A')}\n")
            fh.write(f"# Period: {report_data.get('period', 'N/A')}\n")
            fh.write(f"# Note: {report_data.get('note', '')}\n")

            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in records:
                writer.writerow(row)

        return str(path)


def get_exporter(fmt: str = "json", output_dir: str = ".") -> BaseExporter:
    """Factory function — return the appropriate exporter for *fmt*.

    Supports ``'json'`` and ``'csv'``.  Raises :class:`ValueError` for
    unknown formats.
    """
    fmt = fmt.lower().strip()
    if fmt == "json":
        return JSONExporter(output_dir)
    if fmt == "csv":
        return CSVExporter(output_dir)
    raise ValueError(f"Unsupported export format '{fmt}'. Use 'json' or 'csv'.")

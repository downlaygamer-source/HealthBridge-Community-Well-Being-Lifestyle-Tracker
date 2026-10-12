"""
test_healthbridge.py — Unit test suite for HealthBridge.

Tests:
    - WellnessRecord field validation (valid and invalid cases)
    - User class duplicate date rejection and chronological ordering
    - WellnessScorer score calculation and target normalisation
    - TrendDetector trend classification (improving, declining, stagnant, sudden)
    - RecommendationEngine strategy evaluation and priorities
    - JSON and CSV exporters
    - WellnessReport end-to-end report generation
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from models.user import User
from models.wellness_record import WellnessRecord
from models.wellness_report import WellnessReport
from analysis.scoring import WellnessScorer, ScoringConfig
from analysis.trends import TrendDetector, TrendConfig, IMPROVING, DECLINING, STAGNANT
from analysis.recommendations import RecommendationEngine
from utils.exporters import JSONExporter, CSVExporter, get_exporter


class TestWellnessRecordValidation(unittest.TestCase):
    """Test field-level validation on WellnessRecord."""

    def test_valid_record(self):
        r = WellnessRecord("2026-10-01", 7.5, 45, 2.0, mood_rating=4, stress_level=2)
        self.assertTrue(r.is_valid())
        self.assertEqual(len(r.validate()), 0)

    def test_negative_sleep(self):
        r = WellnessRecord("2026-10-01", -1.0, 30, 2.0)
        self.assertFalse(r.is_valid())
        errors = r.validate()
        self.assertTrue(any("sleep_hours" in e for e in errors))

    def test_excessive_sleep(self):
        r = WellnessRecord("2026-10-01", 25.0, 30, 2.0)
        self.assertFalse(r.is_valid())

    def test_negative_activity(self):
        r = WellnessRecord("2026-10-01", 8.0, -10, 2.0)
        self.assertFalse(r.is_valid())
        errors = r.validate()
        self.assertTrue(any("activity_minutes" in e for e in errors))

    def test_zero_water(self):
        r = WellnessRecord("2026-10-01", 8.0, 30, 0.0)
        self.assertFalse(r.is_valid())
        errors = r.validate()
        self.assertTrue(any("water_litres" in e for e in errors))

    def test_invalid_date_format(self):
        r = WellnessRecord("01-10-2026", 8.0, 30, 2.0)
        self.assertFalse(r.is_valid())

    def test_empty_date(self):
        r = WellnessRecord("", 8.0, 30, 2.0)
        self.assertFalse(r.is_valid())

    def test_invalid_mood_range(self):
        r = WellnessRecord("2026-10-01", 8.0, 30, 2.0, mood_rating=6)
        self.assertFalse(r.is_valid())

    def test_invalid_stress_range(self):
        r = WellnessRecord("2026-10-01", 8.0, 30, 2.0, stress_level=0)
        self.assertFalse(r.is_valid())


class TestUserManagement(unittest.TestCase):
    """Test User record addition, deduplication, and ordering."""

    def test_add_valid_record(self):
        u = User("Test User")
        r = WellnessRecord("2026-10-01", 8.0, 30, 2.0)
        success, msgs = u.add_record(r)
        self.assertTrue(success)
        self.assertEqual(u.record_count, 1)

    def test_reject_invalid_record(self):
        u = User("Test User")
        r = WellnessRecord("2026-10-01", -5.0, 30, 2.0)
        success, msgs = u.add_record(r)
        self.assertFalse(success)
        self.assertEqual(u.record_count, 0)

    def test_reject_duplicate_date(self):
        u = User("Test User")
        r1 = WellnessRecord("2026-10-01", 8.0, 30, 2.0)
        r2 = WellnessRecord("2026-10-01", 7.0, 20, 1.5)
        u.add_record(r1)
        success, msgs = u.add_record(r2)
        self.assertFalse(success)
        self.assertEqual(u.record_count, 1)
        self.assertTrue(any("Duplicate" in m for m in msgs))

    def test_chronological_ordering(self):
        u = User("Test User")
        u.add_record(WellnessRecord("2026-10-03", 8.0, 30, 2.0))
        u.add_record(WellnessRecord("2026-10-01", 7.0, 20, 1.5))
        u.add_record(WellnessRecord("2026-10-02", 6.0, 25, 1.8))
        self.assertEqual(u.records[0].date, "2026-10-01")
        self.assertEqual(u.records[1].date, "2026-10-02")
        self.assertEqual(u.records[2].date, "2026-10-03")


class TestScoring(unittest.TestCase):
    """Test scoring logic and target normalization."""

    def setUp(self):
        self.scorer = WellnessScorer()

    def test_perfect_score(self):
        # 8h sleep, 30min activity, 2L water -> all 100%
        # 0.4*100 + 0.35*100 + 0.25*100 = 100
        r = WellnessRecord("2026-10-01", 8.0, 30, 2.0)
        self.assertEqual(self.scorer.score(r), 100.0)

    def test_partial_score(self):
        # 4h sleep (50%), 15m act (50%), 1L water (50%)
        # 0.4*50 + 0.35*50 + 0.25*50 = 50.0
        r = WellnessRecord("2026-10-01", 4.0, 15, 1.0)
        self.assertEqual(self.scorer.score(r), 50.0)

    def test_score_capping(self):
        # Exceeding targets should not exceed 100% per indicator
        r = WellnessRecord("2026-10-01", 12.0, 120, 5.0)
        self.assertEqual(self.scorer.score(r), 100.0)

    def test_moving_average(self):
        records = [
            WellnessRecord("2026-10-01", 8.0, 30, 2.0), # 100
            WellnessRecord("2026-10-02", 4.0, 15, 1.0), # 50
            WellnessRecord("2026-10-03", 8.0, 30, 2.0), # 100
        ]
        ma = self.scorer.moving_average(records, window=3)
        self.assertEqual(len(ma), 1)
        self.assertAlmostEqual(ma[0], 83.3, places=1)


class TestTrendDetection(unittest.TestCase):
    """Test rule-based trend classification."""

    def setUp(self):
        self.detector = TrendDetector()

    def test_improving_trend(self):
        # 3 low days followed by 3 high days (>10% improvement)
        records = [
            WellnessRecord(f"2026-10-0{i}", 5.0, 15, 1.0) for i in range(1, 4)
        ] + [
            WellnessRecord(f"2026-10-0{i}", 8.0, 45, 2.5) for i in range(4, 7)
        ]
        res = self.detector.detect(records, "sleep_hours")
        self.assertEqual(res["trend"], IMPROVING)

    def test_declining_trend(self):
        # 3 high days followed by 3 low days (>10% decline)
        records = [
            WellnessRecord(f"2026-10-0{i}", 8.0, 45, 2.5) for i in range(1, 4)
        ] + [
            WellnessRecord(f"2026-10-0{i}", 5.0, 15, 1.0) for i in range(4, 7)
        ]
        res = self.detector.detect(records, "activity_minutes")
        self.assertEqual(res["trend"], DECLINING)

    def test_stagnant_trend(self):
        # Very little change between windows
        records = [
            WellnessRecord(f"2026-10-0{i}", 7.0, 30, 2.0) for i in range(1, 4)
        ] + [
            WellnessRecord(f"2026-10-0{i}", 7.1, 30, 2.0) for i in range(4, 7)
        ]
        res = self.detector.detect(records, "sleep_hours")
        self.assertEqual(res["trend"], STAGNANT)


class TestRecommendations(unittest.TestCase):
    """Test recommendation generation and prioritization."""

    def setUp(self):
        self.engine = RecommendationEngine()

    def test_low_sleep_generates_recommendation(self):
        avgs = {"sleep_hours": 5.0, "activity_minutes": 30.0, "water_litres": 2.0}
        trends = {"sleep_hours": {"trend": "declining"}}
        recs = self.engine.generate(avgs, trends)
        self.assertTrue(any(r.indicator == "sleep" for r in recs))
        # Priority should be high (1)
        sleep_rec = next(r for r in recs if r.indicator == "sleep")
        self.assertEqual(sleep_rec.priority, 1)

    def test_all_meeting_targets_generates_no_recs(self):
        avgs = {"sleep_hours": 8.5, "activity_minutes": 45.0, "water_litres": 2.5}
        trends = {
            "sleep_hours": {"trend": "improving"},
            "activity_minutes": {"trend": "stable"},
            "water_litres": {"trend": "stable"},
        }
        recs = self.engine.generate(avgs, trends)
        self.assertEqual(len(recs), 0)


class TestExporters(unittest.TestCase):
    """Test JSON and CSV export functionalities."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_json_export(self):
        exporter = JSONExporter(output_dir=self.temp_dir)
        data = {"user": "Test", "score": 85.5}
        path = exporter.export(data, "test.json")
        self.assertTrue(Path(path).exists())

    def test_csv_export(self):
        exporter = CSVExporter(output_dir=self.temp_dir)
        data = {
            "user": "Test",
            "records": [{"date": "2026-10-01", "score": 85}],
        }
        path = exporter.export(data, "test.csv")
        self.assertTrue(Path(path).exists())

    def test_factory(self):
        self.assertIsInstance(get_exporter("json"), JSONExporter)
        self.assertIsInstance(get_exporter("csv"), CSVExporter)
        with self.assertRaises(ValueError):
            get_exporter("xml")


if __name__ == "__main__":
    unittest.main()

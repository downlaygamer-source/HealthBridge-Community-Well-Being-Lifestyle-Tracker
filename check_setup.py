#!/usr/bin/env python3
"""
check_setup.py — HealthBridge Setup Verification Script.
Like D:\\eliva\\check_setup.py: verifies Python version, dependencies, database, models, and tests.
"""

import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def print_header(text: str):
    print(f"\n{'=' * 65}")
    print(f"  {text}")
    print('=' * 65)


def check_python_version() -> bool:
    v = sys.version_info
    print(f"[*] Python Version: {v.major}.{v.minor}.{v.micro}")
    if v.major < 3 or (v.major == 3 and v.minor < 9):
        print("    ❌ Python 3.9+ required.")
        return False
    print("    ✅ Python version is compatible.")
    return True


def check_dependencies() -> bool:
    print("[*] Checking Dependencies:")
    required = ["flask", "werkzeug", "dotenv"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"    ✅ {pkg}: installed")
        except ImportError:
            missing.append(pkg)
            print(f"    ❌ {pkg}: missing")

    if missing:
        print(f"    Run: pip install -r requirements.txt")
        return False
    return True


def check_database() -> bool:
    print("[*] Checking SQLite Database & Seeding:")
    try:
        from models.database import init_db, get_db
        init_db()
        conn = get_db()
        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        records_count = conn.execute("SELECT COUNT(*) FROM wellness_records").fetchone()[0]
        conn.close()

        print(f"    ✅ Database active: {users_count} users, {records_count} pre-seeded wellness records.")
        return True
    except Exception as e:
        print(f"    ❌ Database check failed: {e}")
        return False


def check_oop_domain() -> bool:
    print("[*] Checking Core OOP Domain Models:")
    try:
        from models.wellness_record import WellnessRecord
        from models.user import User
        from models.wellness_report import WellnessReport
        from analysis.scoring import WellnessScorer, ScoringConfig
        from analysis.trends import TrendDetector
        from analysis.recommendations import RecommendationEngine
        from utils.exporters import JSONExporter, CSVExporter

        # Test instantiate
        u = User("Verification User")
        r = WellnessRecord("2026-10-12", 7.5, 30, 2.0, 4, 2)
        valid, _ = u.add_record(r)
        assert valid, "Failed to add valid record"

        scorer = WellnessScorer()
        score = scorer.score(r)
        assert 0 <= score <= 105, f"Score out of bounds: {score}"

        print("    ✅ OOP models, validation, scoring, and exporters verified.")
        return True
    except Exception as e:
        print(f"    ❌ OOP Domain verification failed: {e}")
        return False


def run_unit_tests() -> bool:
    print("[*] Running Automated Unit Tests:")
    try:
        from main import run_tests
        success = run_tests()
        if success:
            print("    ✅ All automated unit and web tests passed.")
        else:
            print("    ❌ Some tests failed.")
        return success
    except Exception as e:
        print(f"    ❌ Test execution error: {e}")
        return False


def main():
    print_header("🌿 HealthBridge Setup & Environment Verification")

    results = [
        check_python_version(),
        check_dependencies(),
        check_database(),
        check_oop_domain(),
        run_unit_tests(),
    ]

    print("\n" + "=" * 65)
    if all(results):
        print("  🎉 ALL CHECKS PASSED — HealthBridge is ready to run!")
        print("  👉 Start the web server:  python run.py")
        print("  👉 Or run CLI demo:       python run.py --cli")
    else:
        print("  ⚠️  Some checks failed. Please review errors above.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()

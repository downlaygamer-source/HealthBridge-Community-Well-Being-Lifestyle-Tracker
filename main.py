"""
main.py — Master entry point for HealthBridge Platform (CLI & Web).

Commands:
    python main.py          -> Launch the HealthBridge Web Application (Default)
    python main.py --web    -> Launch the HealthBridge Web Application
    python main.py --cli    -> Run the terminal demonstration report & exports
    python main.py --test   -> Run all 38 automated unit & web tests
    python main.py --all    -> Run CLI demo, execute tests, and launch web server
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure local imports resolve when running directly from the project directory
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.sample_data import build_sample_users, get_invalid_sample_records
from models.wellness_report import WellnessReport
from analysis.scoring import ScoringConfig
from models.user import User
from models.wellness_record import WellnessRecord


def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   🌿  H E A L T H B R I D G E                                     ║
    ║   Community Well-Being & Lifestyle Tracker                        ║
    ║                                                                   ║
    ║   Theme:  Python Fundamentals + OOP + SDGs                        ║
    ║   Goals:  SDG 3 (Good Health) & SDG 10 (Reduced Inequalities)     ║
    ║   Scope:  Non-diagnostic Lifestyle & Habit Observation            ║
    ║   Stack:  Flask + SQLite + Chart.js + Pure Python OOP Core        ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def demo_invalid_data_handling():
    """Demonstrate robust validation against diverse invalid inputs."""
    print("\n" + "=" * 70)
    print("  SCENARIO 1: ROBUST INPUT VALIDATION & DATA CLEANING")
    print("=" * 70)
    print("HealthBridge guards data integrity before recording. The system rejects")
    print("out-of-range, negative, duplicate, or malformed entries without crashing.\n")

    test_user = User("Demo User")
    invalids = get_invalid_sample_records()

    for idx, case in enumerate(invalids, 1):
        rec: WellnessRecord = case["record"]
        desc: str = case["description"]
        success, messages = test_user.add_record(rec)

        status_icon = "❌ REJECTED (Expected)" if not success else "⚠️ ACCEPTED (Unexpected)"
        print(f"  [{idx}] Test: {desc}")
        print(f"      Input:    {rec}")
        print(f"      Result:   {status_icon}")
        for m in messages:
            print(f"      Reason:   {m}")
        print()

    # Demonstrate duplicate rejection
    print("  [*] Testing Duplicate Date Rejection:")
    valid_rec = WellnessRecord("2026-10-12", 7.0, 30, 2.0)
    s1, _ = test_user.add_record(valid_rec)
    print(f"      First entry ('2026-10-12'): {'✅ Added' if s1 else 'Failed'}")

    dup_rec = WellnessRecord("2026-10-12", 8.0, 45, 2.5)
    s2, m2 = test_user.add_record(dup_rec)
    print(f"      Duplicate entry ('2026-10-12'): {'❌ Rejected (Expected)' if not s2 else 'Accepted'}")
    for m in m2:
        print(f"      Reason:   {m}")


def demo_multi_user_reports(users: dict[str, User]):
    """Demonstrate weekly report generation, trends, and recommendations across users."""
    print("\n" + "=" * 70)
    print("  SCENARIO 2: MULTI-USER LIFESTYLE PROFILES & WEEKLY REPORTS")
    print("=" * 70)
    print("Comparing 3 distinct user personas over 14 days of tracked habits:\n")
    print("  1. Asha Sharma  — Steady improver (habit building)")
    print("  2. Rohan Patel  — Sedentary desk worker (elevated stress, low activity)")
    print("  3. Priya Nair   — Student facing exam stress (abrupt changes)")

    output_dir = Path("exports")
    output_dir.mkdir(exist_ok=True)

    for key, user in users.items():
        report = WellnessReport(user)
        report.print_weekly_report(days=7)

        # Export both formats
        json_path = report.export(fmt="json", output_dir=str(output_dir))
        csv_path = report.export(fmt="csv", output_dir=str(output_dir))
        print(f"  📁 Exported JSON: {json_path}")
        print(f"  📁 Exported CSV:  {csv_path}\n")


def demo_configurable_scoring(user: User):
    """Demonstrate how weights and targets can be adjusted dynamically."""
    print("\n" + "=" * 70)
    print("  SCENARIO 3: CONFIGURABLE WELLNESS SCORING")
    print("=" * 70)
    print("Demonstrating system flexibility: different users or programs can")
    print("rebalance indicator weights to fit specific wellness initiatives.\n")

    # Default weights: Sleep 40%, Activity 35%, Water 25%
    default_report = WellnessReport(user)
    def_data = default_report.generate_weekly_report(days=7)
    def_score = def_data["summary"]["average_score"]

    # Custom fitness-focused weights: Activity 50%, Sleep 30%, Water 20%
    fitness_config = ScoringConfig(
        weight_sleep=0.30,
        weight_activity=0.50,
        weight_water=0.20,
        activity_target=45,  # Higher activity target (45m)
    )
    fitness_report = WellnessReport(user, scoring_config=fitness_config)
    fit_data = fitness_report.generate_weekly_report(days=7)
    fit_score = fit_data["summary"]["average_score"]

    print(f"  User: {user.name}")
    print(f"  - Default Program Score (Sleep 40%, Act 35%, H2O 25%):   {def_score} / 100")
    print(f"  - Fitness Program Score (Sleep 30%, Act 50%, H2O 20%):   {fit_score} / 100")
    print(f"  Difference: {round(fit_score - def_score, 1):+0.1f} points based on program priorities.")


def run_cli_demo():
    """Execute the full terminal-based demonstration."""
    print_banner()
    users = build_sample_users()
    demo_invalid_data_handling()
    demo_multi_user_reports(users)
    demo_configurable_scoring(users["rohan"])

    print("\n" + "=" * 70)
    print("  ✅ CLI DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("  Summary:")
    print("  - Handled 14 days of data for 3 diverse user profiles")
    print("  - Rejected 8 invalid input scenarios and duplicate entries")
    print("  - Evaluated moving averages, trends, and sudden variations")
    print("  - Generated tailored, non-medical lifestyle guidance")
    print("  - Exported structured reports to exports/ directory")
    print("=" * 70 + "\n")


def run_tests():
    """Run the complete unittest suite."""
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover("tests")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_web(port=5000):
    """Launch the Flask web platform."""
    from app import app
    print_banner()
    print("  🚀 Starting HealthBridge Interactive Web UI")
    print(f"  🌐 Local Server:  http://127.0.0.1:{port}")
    print("  ⚡ Demo Accounts: 1-click logins available on the sign-in page!")
    print("  🧪 Validation:   http://127.0.0.1:5000/validation-lab")
    print("=" * 70 + "\n")
    app.run(debug=True, port=port)


def main():
    parser = argparse.ArgumentParser(description="HealthBridge Community Well-Being Platform")
    parser.add_argument("--web", "-w", action="store_true", help="Launch Flask web interface (Default)")
    parser.add_argument("--cli", "-c", action="store_true", help="Run terminal demonstration report")
    parser.add_argument("--test", "-t", action="store_true", help="Run automated test suite (38 tests)")
    parser.add_argument("--all", "-a", action="store_true", help="Run CLI demo, tests, and web app")
    parser.add_argument("--port", "-p", type=int, default=5000, help="Web server port (Default: 5000)")

    args = parser.parse_args()

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    elif args.cli:
        run_cli_demo()
    elif args.all:
        run_cli_demo()
        run_tests()
        run_web(port=args.port)
    else:
        # Default behavior: run web app
        run_web(port=args.port)


if __name__ == "__main__":
    main()

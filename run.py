"""
run.py — Application Launcher for HealthBridge.
Like D:\\eliva launcher: starts the web server, CLI demonstration, or test suite.
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure local imports resolve
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import run_cli_demo, run_tests, run_web, print_banner


def main():
    parser = argparse.ArgumentParser(description="HealthBridge Community Well-Being Platform")
    parser.add_argument("--port", "-p", type=int, default=5000, help="Port to run the web server on (Default: 5000)")
    parser.add_argument("--cli", "-c", action="store_true", help="Run the terminal demonstration report & exports")
    parser.add_argument("--test", "-t", action="store_true", help="Run the automated test suite (41 tests)")
    parser.add_argument("--all", "-a", action="store_true", help="Run CLI demo, tests, and launch web server")
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
        # Default: launch web server
        run_web(port=args.port)


if __name__ == "__main__":
    main()

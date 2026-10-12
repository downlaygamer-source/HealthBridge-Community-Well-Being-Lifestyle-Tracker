"""
config.py — Configuration settings for HealthBridge Web Application.
"""

from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

SECRET_KEY = os.getenv("SECRET_KEY", "healthbridge-hackathon-2026-secret-key-national")
DATABASE_PATH = os.getenv("DATABASE_PATH", str(INSTANCE_DIR / "healthbridge.db"))

# Application Metadata
APP_NAME = "HealthBridge"
APP_SUBTITLE = "Community Well-Being & Lifestyle Tracker"
APP_THEME = "SDG 3 (Good Health & Well-Being) · SDG 10 (Reduced Inequalities)"
APP_VERSION = "2.0.0 (Web + CLI)"

# Default indicator targets
DEFAULT_TARGETS = {
    "sleep_hours": 8.0,
    "activity_minutes": 30,
    "water_litres": 2.0,
    "mood_rating": 4,
    "stress_level": 2,
}

# Default scoring weights (Sleep 40%, Activity 35%, Water 25%)
DEFAULT_WEIGHTS = {
    "weight_sleep": 0.40,
    "weight_activity": 0.35,
    "weight_water": 0.25,
}

# Non-medical disclaimer strictly required by problem statement
NON_MEDICAL_DISCLAIMER = (
    "DISCLAIMER: HealthBridge is a non-diagnostic community lifestyle tracker "
    "designed for wellness awareness, habit reflection, and educational purposes. "
    "It does not provide medical diagnoses, clinical assessments, or treatment prescriptions. "
    "For medical symptoms or health conditions, please consult a licensed healthcare professional."
)

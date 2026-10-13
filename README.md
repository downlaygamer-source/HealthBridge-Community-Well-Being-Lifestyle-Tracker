# 🌿 HealthBridge — Community Well-Being & Lifestyle Tracker

> **HACK-AI-THON 2026 | National Level Group Challenge**  
> **Theme:** Python Fundamentals + Object-Oriented Programming (OOP) + Sustainable Development Goals (SDGs)  
> **SDG Alignment:** **SDG 3** (Good Health and Well-Being) & **SDG 10** (Reduced Inequalities)  
> **Scope:** Non-diagnostic community lifestyle tracking, trend detection, and explainable recommendations.

---

## 📌 Project Overview

**HealthBridge** is a community wellness tracking platform that allows diverse users to record and analyze daily lifestyle habits—**sleep duration**, **physical activity**, **water hydration**, **mood rating**, and **stress levels**.

Built with a rigorous **Object-Oriented Python core**, local **SQLite persistence**, and a **modern web interface** inspired by Group-15's design system, HealthBridge transforms raw self-reported lifestyle records into:
- **Configurable composite wellness scores** (0–100)
- **3-day and 7-day moving averages**
- **Week-over-week variance calculations**
- **Rule-based trend classifications** (*Sustained Improvement*, *Sustained Decline*, *Stagnant*, *Sudden Changes*)
- **Personalized, non-medical recommendations** with transparent reasoning
- **Downloadable structured exports** in both **JSON** and **CSV** formats
- **Interactive Assistant Chatbot** providing contextual insights and formula explanations

> ⚠️ **Non-Diagnostic Notice:** HealthBridge is strictly an educational and self-reflection lifestyle tool. It does **not** diagnose medical conditions, evaluate clinical pathology, or prescribe medical treatments.

---

## 🎯 Sustainable Development Goals (SDGs) Alignment

| SDG Target | HealthBridge Real-World Application |
|---|---|
| **SDG 3: Good Health & Well-Being** (*Target 3.4*) | Promotes early personal reflection on primary non-communicable lifestyle risk factors (chronic sleep debt, sedentary routines, dehydration) before clinical intervention is needed. |
| **SDG 10: Reduced Inequalities** (*Target 10.2*) | Ensures health tracking is completely accessible and barrier-free. Focuses exclusively on **zero-cost, accessible habits** (neighborhood walking, tap water hydration, sleep regularity) rather than expensive wearable devices, gym memberships, or subscription diets. |

---

## 🏗️ Architecture & Project Structure

Structured cleanly and modularly (following the `D:\eliva` engineering pattern):

```
D:\HealthBridge\
├── run.py                      # Master application launcher (Web, CLI, Test)
├── check_setup.py              # Environment & setup verification script
├── app.py                      # Flask Web Application & REST API
├── config.py                   # Global configuration, defaults & disclaimer
├── main.py                     # Entry point orchestrator
├── requirements.txt            # Package dependencies
├── .env                        # Local environment variables
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore rules
├── QUICKSTART.md               # 2-minute quick-start reference
├── README.md                   # Complete documentation
│
├── models/                     # Core Domain OOP Models
│   ├── user.py                 # User class (Composition: User HAS-A WellnessRecords)
│   ├── wellness_record.py      # WellnessRecord dataclass (Encapsulation + field validation)
│   ├── wellness_report.py      # WellnessReport class (Orchestrator: Scorer + Trends + Recs)
│   └── database.py             # SQLite persistence, schema migrations & auto-seeding
│
├── analysis/                   # Algorithmic Analysis Modules
│   ├── scoring.py              # WellnessScorer & ScoringConfig (Weighted composite scoring)
│   ├── trends.py               # TrendDetector (Sliding-window rule-based trend engine)
│   └── recommendations.py      # RecommendationEngine (Strategy Pattern / Polymorphism)
│
├── utils/                      # Helper & Export Utilities
│   ├── validators.py           # Decoupled validation functions
│   └── exporters.py            # BaseExporter -> JSONExporter, CSVExporter (Inheritance)
│
├── services/                   # Service Layer
│   ├── wellness_service.py     # Database-to-OOP adapter & KPI metrics calculation
│   ├── report_service.py       # Weekly report generation & export serialization
│   └── chatbot_service.py      # Contextual offline HealthBridge Assistant
│
├── static/                     # Web Frontend Assets
│   ├── css/style.css           # Custom design system (Light/Dark themes, glassmorphism, KPIs)
│   └── js/app.js               # Client interactivity, Chart.js visualizers & simulator
│
├── templates/                  # Jinja2 HTML Templates
│   ├── base.html               # Responsive app shell, sidebar navigation & assistant chatbot
│   ├── landing.html            # Public landing page with SDG 3 & 10 showcase
│   ├── login.html              # Secure credentials-based sign-in page
│   ├── signup.html             # Member registration
│   ├── dashboard.html          # Overview dashboard with KPI tiles, trend line & alerts
│   ├── records.html            # Daily records table, add modal & domain rules
│   ├── analytics.html          # Interactive Chart.js timelines & balance radar
│   ├── intelligence.html       # Explainable scores, rule justifications & What-If simulator
│   ├── reports.html            # Official weekly report preview with JSON & CSV downloads
│   ├── coach.html              # Community coach & SDG advocacy tips
│   ├── goals.html              # Habit milestones & daily streaks
│   ├── validation_lab.html     # Interactive edge-case testing lab for judges
│   ├── users.html              # Community members directory
│   ├── profile.html            # User profile and account details
│   └── settings.html           # Configurable targets, weights & theme selector
│
├── data/
│   └── sample_data.py          # 14 days of realistic multi-user test data + edge cases
│
└── tests/
    ├── test_healthbridge.py    # 25 domain OOP unit tests
    └── test_web.py             # 16 web route, session, export & chatbot tests
```

### OOP Concepts Applied:
1. **Encapsulation:** Data models (`WellnessRecord`, `User`) enforce internal invariant validation before state mutation.
2. **Composition:** `User` has-a collection of `WellnessRecord` objects. `WellnessReport` has-a `User`, `WellnessScorer`, `TrendDetector`, and `RecommendationEngine`.
3. **Inheritance & Polymorphism:** 
   - `BaseExporter` abstracts export serialization; subclasses `JSONExporter` and `CSVExporter` override `.export()`.
   - `BaseRecommendationStrategy` defines polymorphic evaluation overridden by `SleepRecommendation`, `ActivityRecommendation`, `HydrationRecommendation`, `MoodRecommendation`, and `StressRecommendation`.
4. **Strategy Pattern:** `RecommendationEngine` routes indicator analysis dynamically based on configured strategies.
5. **Configurability:** `ScoringConfig` allows dynamic runtime reweighting of indicators (e.g. standard program vs. fitness-focused initiative).

---

## ⚡ Quick Start & Execution Guide

### 1. Requirements
- Python 3.9+ (Python 3.12 recommended)
- Dependencies: `Flask>=3.0`, `Werkzeug>=3.0`, `python-dotenv>=1.0`

Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Verify Setup (Pre-Flight Checks)
```bash
python check_setup.py
```
Checks Python version, installs dependencies check, database verification, OOP models, and runs the 47-test suite.

### 3. Launch the Web Platform (Recommended)
```bash
python run.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser (automatically redirects to the sign-in page).

### 4. Run the Terminal CLI Demonstration
```bash
python run.py --cli
```
Prints the complete scenario report directly to your terminal and saves exported JSON & CSV files to `exports/`.

### 5. Run Automated Test Suite
```bash
python run.py --test
# or:
python -m unittest discover -s tests
```
Runs all **51 automated unit & web tests** verifying:
- Input validation boundaries & duplicate rejection
- Moving averages & week-over-week variance
- Trend classification logic
- Recommendation generation
- CSV & JSON exporters
- Web authentication, dashboard rendering, export downloads, and assistant Q&A
- Role-based access control (RBAC), user isolation, and role management permissions
- **Password-protected account switching** (strictly blocks passwordless account switching)

---

## 👥 Demonstration Accounts & Role Management

HealthBridge features built-in Role-Based Access Control (RBAC) enforced on the backend. You can evaluate the platform using the **Admin Accounts** or the **Demo Account**:

| Account Type | Name & Credentials | Role | Key Permissions & Functionality |
|---|---|---|---|
| **Admin Account 1** | **Name:** `Jivraj`<br>**Email:** `admin@healthbridge.local`<br>**Password:** `HBadmin#2026!` | `admin` | **System Governance & Role Management:**<br>• Access the exclusive Admin Control Panel at `/admin`.<br>• View all registered platform users in a structured table with record counts.<br>• **Manage User Roles:** Exclusively authorized to assign or change user roles across `Normal User`, `Manager`, and `Admin`.<br>• Protected by an automatic invariant preventing accidental removal or demotion of the last active administrator. |
| **Admin Account 2** | **Name:** `Vaibhav`<br>**Email:** `vaibhav@healthbridge.local`<br>**Password:** `HBadmin#2026!` | `admin` | **Co-Administrator Oversight:**<br>• Full administrator privileges, system oversight, and role management capabilities at `/admin`. |
| **Demo Account** | **Name:** `Alex Rivera (Demo Profile)`<br>**Email:** `demo@healthbridge.local`<br>**Password:** `HBdemo#2026!` | `demo` | **Safe Feature Showcase:**<br>• Pre-loaded with 14 days of realistic fictional records clearly labeled as `[Demo Data]`.<br>• Explore dashboards, daily logging, sliding-window trends, and weekly report exports safely.<br>• Prominently flagged with an in-app demonstration banner. |

### Role Hierarchy & Permissions Summary
- **Administrator (`admin`):** Full oversight. Exclusively authorized to access `/admin` and reassign roles across `Normal User`, `Manager`, and `Admin`. Barred from demoting the final administrator.
- **Manager (`manager`):** Accesses `/manager` to inspect daily logs and generate weekly reports for authorized community members. Strictly forbidden (HTTP 403) from accessing admin routes or modifying roles.
- **Normal User (`normal_user`):** Accesses their personal dashboard, records, and reports. Strictly restricted (HTTP 403) from accessing another user's private data or administrative pages.
- **Authentication & Account Security:** Account switching is completely disabled. To access another account, users must sign out and authenticate through the standard `/login` portal with their valid email/username and password. Direct login without credentials is strictly prohibited for all non-demo accounts.

---

## 🧪 Interactive Validation Lab (`/validation-lab`)

Built specifically for judges to test edge cases interactively:
- **Negative Sleep:** `-2.5 hours` → ❌ *Rejected by `validate_range`*
- **Excessive Sleep:** `26.0 hours` → ❌ *Rejected (bounds 0–24)*
- **Negative Activity:** `-15 minutes` → ❌ *Rejected (bounds ≥ 0)*
- **Zero / Negative Water:** `0.0 Litres` → ❌ *Rejected by `validate_positive`*
- **Duplicate Date:** Submitting a date already logged for that user → ❌ *Rejected by `User.add_record`*
- **Missing Date:** Empty date string → ❌ *Rejected by `validate_date`*
- **Out-of-Bounds Mood/Stress:** Values outside `1–5` scale → ❌ *Rejected*

---

## 📊 Export Formats

Generated weekly reports can be exported directly from the UI or CLI:
1. **Structured JSON:** Complete report dictionary containing metadata, indicator summaries, period averages, week-over-week changes, trend analysis, daily breakdowns, recommendations, and disclaimer.
2. **Tabular CSV:** Standard CSV containing header metadata, daily indicator rows, trend classifications, and actionable suggestions.

---

## ⚖️ Mandatory Ethical & Health Disclaimer
HealthBridge is an educational lifestyle tracking system. It **does not** provide clinical diagnostic evaluations, medical prognosis, or therapeutic treatment advice. Individuals experiencing physical or mental health symptoms should always consult a licensed medical professional.

---

# Made by 
- **Coding** - Jivraj & Vaibhav 
- **Documentation** - Swarit & Yunay
- **Presentation** - Venisha & Pradishan
- **Demonstration** - Jivraj & Vaibhav

---
*Built with ❤️ for HACK-AI-THON 2026 National Level Challenge.*

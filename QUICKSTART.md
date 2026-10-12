# 🌿 HealthBridge — Quick Start Reference

## 30-Second Overview
HealthBridge is a community well-being & lifestyle tracker aligned with **SDG 3** (Good Health and Well-Being) and **SDG 10** (Reduced Inequalities). It tracks 5 daily lifestyle indicators (Sleep, Physical Activity, Water Hydration, Mood, Stress) using pure Python Object-Oriented Programming, rule-based sliding-window trend detection, and a full-stack Flask web application.

---

## ⚡ Quick Start (2 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Verify Setup
```bash
python check_setup.py
```
This runs pre-flight environment checks, validates the SQLite database, verifies OOP models, and executes the 51-test suite.

### Step 3: Run HealthBridge
```bash
python run.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser (redirects automatically to `/login`).

---

## 👥 Accounts & Role Management

HealthBridge includes built-in Role-Based Access Control (RBAC). Use either of the **Admin Accounts** or the **Demo Account**:

| Account Type | Name & Credentials | Role | Key Permissions |
|---|---|---|---|
| **Admin Account 1** | **Name:** `Jivraj`<br>**Email:** `admin@healthbridge.local`<br>**Password:** `HBadmin#2026!` | `admin` | **System Governance & Role Management:**<br>• Access the Admin Dashboard at `/admin`.<br>• View all registered users and their record counts.<br>• **Manage Roles:** Exclusively authorized to assign or change user roles across `Normal User`, `Manager`, and `Admin`.<br>• Protected from demoting the last remaining administrator. |
| **Admin Account 2** | **Name:** `Vaibhav`<br>**Email:** `vaibhav@healthbridge.local`<br>**Password:** `HBadmin#2026!` | `admin` | **Co-Administrator Oversight:**<br>• Full administrator privileges, system oversight, and role management capabilities at `/admin`. |
| **Demo Account** | **Name:** `Alex Rivera (Demo Profile)`<br>**Email:** `demo@healthbridge.local`<br>**Password:** `HBdemo#2026!` | `demo` | **Safe Feature Exploration:**<br>• Pre-loaded with 14 days of realistic records tagged `[Demo Data]`.<br>• Safe exploration of dashboards, records, trends, and reports without entering real data. |

---

## 🧪 Judge & Evaluator Workbenches

1. **Interactive Validation Lab (`/validation-lab`):**
   Test negative sleep, excessive sleep, negative activity, zero water, and duplicate dates live with real-time domain rejection feedback.

2. **What-If Lifestyle Simulator (`/intelligence`):**
   Adjust sleep, activity, and hydration sliders to predict score shifts in real time before logging.

3. **Offline Assistant Chatbot:**
   Click the **🌿 Assistant button** at the bottom-right of any page to ask questions about scores, trends, SDGs, and OOP formulas.

---

## 💻 CLI Commands

```bash
# Launch Web Platform (Default)
python run.py

# Run Terminal Scenario Demo & Exports
python run.py --cli

# Run Automated Test Suite (51 Tests)
python run.py --test

# Change Server Port
python run.py --port 8000
```

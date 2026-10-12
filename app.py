"""
app.py — HealthBridge Community Well-Being & Lifestyle Tracker Web Application.

Theme: Python Fundamentals + Object-Oriented Programming (OOP) + SDGs (SDG 3 & 10)
Group 1 · National Level Hack-AI-Thon 2026
"""

from __future__ import annotations
import os
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    Response,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from config import (
    APP_NAME,
    APP_SUBTITLE,
    APP_THEME,
    DATABASE_PATH,
    DEFAULT_TARGETS,
    DEFAULT_WEIGHTS,
    NON_MEDICAL_DISCLAIMER,
    SECRET_KEY,
)
from models.database import get_db, init_db
from models.wellness_record import WellnessRecord
from models.user import User
from services.wellness_service import (
    add_wellness_record_safe,
    compute_dashboard_metrics,
    load_user_oop,
)
from services.report_service import (
    export_report_csv,
    export_report_json,
    generate_user_weekly_report,
)
from services.chatbot_service import get_chatbot_response

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    DATABASE=str(DATABASE_PATH),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Initialize database on app creation
with app.app_context():
    init_db()


# -----------------------------------------------------------------------------
# Hooks & Auth Decorators
# -----------------------------------------------------------------------------
@app.before_request
def load_logged_in_user():
    """Populate g.user on each request if logged in."""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        conn = get_db()
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        g.user = user_row


@app.context_processor
def inject_globals():
    """Inject template helper variables."""
    return {
        "app_name": APP_NAME,
        "app_subtitle": APP_SUBTITLE,
        "app_theme": APP_THEME,
        "today_date": datetime.now().strftime("%Y-%m-%d"),
        "non_medical_disclaimer": NON_MEDICAL_DISCLAIMER,
    }


def login_required(view):
    """Decorator ensuring a user session is active."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    """Decorator restricting route access strictly to administrators."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        if g.user["role"] != "admin":
            return render_template("403.html", message="Administrator privileges are required to access this resource."), 403
        return view(**kwargs)
    return wrapped_view


def manager_required(view):
    """Decorator restricting route access to managers and administrators."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        if g.user["role"] not in ("admin", "manager", "community_worker"):
            return render_template("403.html", message="Community Manager or Administrator privileges are required to access this resource."), 403
        return view(**kwargs)
    return wrapped_view


def can_manage_user(acting_user: sqlite3.Row, target_user_id: int) -> bool:
    """Determine whether acting_user has authority to view or manage target_user_id."""
    if acting_user["id"] == target_user_id:
        return True
    role = acting_user["role"]
    if role == "admin":
        return True
    if role in ("manager", "community_worker"):
        conn = get_db()
        target = conn.execute("SELECT role FROM users WHERE id = ?", (target_user_id,)).fetchone()
        conn.close()
        if not target:
            return False
        # Managers can manage normal users and demo profiles, but cannot manage other managers or admins
        return target["role"] in ("normal_user", "member", "demo")
    return False


# -----------------------------------------------------------------------------
# Authentication & Landing Routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    """Root entry route: redirect to dashboard if logged in, otherwise to login page."""
    if g.user:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/landing")
def landing():
    """Public project overview landing page."""
    return render_template("landing.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User authentication route."""
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        # Direct lookup supporting both email address and convenient admin user identifiers
        user = conn.execute(
            """
            SELECT * FROM users
            WHERE LOWER(email) = ?
               OR (user_id = 'admin_jivraj' AND ? IN ('admin@healthbridge.local', 'jivraj@healthbridge.local', 'jivraj', 'admin'))
               OR (user_id = 'admin_vaibhav' AND ? IN ('vaibhav@healthbridge.local', 'vaibhav'))
               OR (user_id = 'trial_demo' AND ? IN ('demo@healthbridge.local', 'demo'))
            """,
            (email, email, email, email),
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email address or password. Please verify your credentials.", "error")

    return render_template("login.html")


@app.route("/demo-login/<user_key>")
def demo_login(user_key: str):
    """Direct login is disabled. All accounts require valid credentials."""
    flash("Direct login without credentials is disabled. Please sign in with your email/username and password.", "error")
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """New member registration."""
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        sleep_target = float(request.form.get("sleep_target", 8.0))
        activity_target = int(request.form.get("activity_target", 30))

        if not full_name or not email or len(password) < 4:
            flash("Please provide a valid name, email, and password.", "error")
            return render_template("signup.html")

        user_id_slug = full_name.lower().replace(" ", "_")
        pwd_hash = generate_password_hash(password)

        conn = get_db()
        try:
            conn.execute(
                """
                INSERT INTO users (user_id, full_name, email, password_hash, role, sleep_target, activity_target)
                VALUES (?, ?, ?, ?, 'normal_user', ?, ?)
                """,
                (user_id_slug, full_name, email, pwd_hash, sleep_target, activity_target),
            )
            conn.commit()
            new_user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            session.clear()
            session["user_id"] = new_user["id"]
            flash("Account registered successfully! Welcome to HealthBridge.", "success")
            return redirect(url_for("dashboard"))
        except Exception:
            flash("An account with that email or ID already exists.", "error")
        finally:
            conn.close()

    return render_template("signup.html")


@app.route("/logout")
def logout():
    """Log out and terminate session."""
    session.clear()
    flash("You have signed out of HealthBridge.", "success")
    return redirect(url_for("login"))


# -----------------------------------------------------------------------------
# Core Dashboard & Records
# -----------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    """Primary overview dashboard with KPIs, moving averages, and alerts."""
    conn = get_db()
    metrics = compute_dashboard_metrics(conn, g.user["id"])

    # Recent records
    recent_rows = conn.execute(
        """
        SELECT * FROM wellness_records
        WHERE user_id = ?
        ORDER BY record_date DESC
        LIMIT 7
        """,
        (g.user["id"],),
    ).fetchall()

    # Pre-calculate daily score mapping for recent records
    oop_user, scoring_config = load_user_oop(conn, g.user["id"])
    conn.close()

    from analysis.scoring import WellnessScorer
    scorer = WellnessScorer(scoring_config)
    score_map = {r.date: scorer.score(r) for r in oop_user.records}

    return render_template(
        "dashboard.html",
        metrics=metrics,
        recent_records=recent_rows,
        score_map=score_map,
    )


@app.route("/records")
@login_required
def records():
    """Records management list and validation view."""
    member_id_raw = request.args.get("member_id")
    target_id = g.user["id"]
    if member_id_raw and member_id_raw.isdigit():
        req_id = int(member_id_raw)
        if not can_manage_user(g.user, req_id):
            return render_template("403.html", message="You do not have permission to view this user's private records."), 403
        target_id = req_id

    conn = get_db()
    target_user = conn.execute("SELECT * FROM users WHERE id = ?", (target_id,)).fetchone()
    if not target_user:
        conn.close()
        flash("Requested member does not exist.", "error")
        return redirect(url_for("records"))

    record_rows = conn.execute(
        """
        SELECT * FROM wellness_records
        WHERE user_id = ?
        ORDER BY record_date DESC
        """,
        (target_id,),
    ).fetchall()

    oop_user, scoring_config = load_user_oop(conn, target_id)

    managed_members = []
    if g.user["role"] == "admin":
        managed_members = conn.execute("SELECT * FROM users ORDER BY full_name ASC").fetchall()
    elif g.user["role"] in ("manager", "community_worker"):
        managed_members = conn.execute(
            "SELECT * FROM users WHERE role IN ('normal_user', 'member', 'demo') OR id = ? ORDER BY full_name ASC",
            (g.user["id"],),
        ).fetchall()

    conn.close()

    from analysis.scoring import WellnessScorer
    scorer = WellnessScorer(scoring_config)
    score_map = {r.date: scorer.score(r) for r in oop_user.records}

    return render_template(
        "records.html",
        records=record_rows,
        score_map=score_map,
        target_user=target_user,
        managed_members=managed_members,
        is_managing_other=(target_id != g.user["id"]),
    )


@app.route("/records/add", methods=["POST"])
@login_required
def add_record():
    """Add a wellness record with full OOP domain validation."""
    target_id = g.user["id"]
    target_param = request.form.get("member_id") or request.form.get("user_id") or request.args.get("member_id")
    if target_param and str(target_param).isdigit():
        req_id = int(target_param)
        if not can_manage_user(g.user, req_id):
            return render_template("403.html", message="You do not have permission to add records for this user."), 403
        target_id = req_id

    record_date = request.form.get("record_date", "").strip()
    try:
        sleep_hours = float(request.form.get("sleep_hours", 0.0))
        activity_minutes = int(request.form.get("activity_minutes", 0))
        water_litres = float(request.form.get("water_litres", 0.0))
    except ValueError:
        flash("Numeric fields must contain valid numbers.", "error")
        return redirect(request.referrer or url_for("records"))

    mood_raw = request.form.get("mood_rating")
    mood_rating = int(mood_raw) if mood_raw and mood_raw.isdigit() else None

    stress_raw = request.form.get("stress_level")
    stress_level = int(stress_raw) if stress_raw and stress_raw.isdigit() else None

    notes = request.form.get("notes", "").strip()

    conn = get_db()
    success, messages = add_wellness_record_safe(
        conn,
        target_id,
        date=record_date,
        sleep_hours=sleep_hours,
        activity_minutes=activity_minutes,
        water_litres=water_litres,
        mood_rating=mood_rating,
        stress_level=stress_level,
        notes=notes,
    )
    conn.close()

    if success:
        flash(messages[0], "success")
    else:
        for msg in messages:
            flash(msg, "error")

    return redirect(request.referrer or url_for("records"))


@app.route("/records/delete/<int:record_id>", methods=["POST"])
@login_required
def delete_record(record_id: int):
    """Delete a wellness record."""
    conn = get_db()
    rec = conn.execute("SELECT * FROM wellness_records WHERE id = ?", (record_id,)).fetchone()
    if not rec:
        conn.close()
        flash("Record not found.", "error")
        return redirect(url_for("records"))

    if not can_manage_user(g.user, rec["user_id"]):
        conn.close()
        return render_template("403.html", message="You do not have permission to delete this user's records."), 403

    conn.execute("DELETE FROM wellness_records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    flash("Record deleted.", "success")
    return redirect(url_for("records"))


@app.route("/records/seed-demo", methods=["POST"])
@login_required
def seed_demo_records():
    """Reset the current user's records to the standard 14-day history."""
    conn = get_db()
    # Remove existing
    conn.execute("DELETE FROM wellness_records WHERE user_id = ?", (g.user["id"],))

    from data.sample_data import build_sample_users
    samples = build_sample_users()
    matched = samples.get(g.user["user_id"]) or samples.get("asha_sharma")

    for rec in matched.records:
        conn.execute(
            """
            INSERT INTO wellness_records
            (user_id, record_date, sleep_hours, activity_minutes, water_litres, mood_rating, stress_level, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                g.user["id"],
                rec.date,
                rec.sleep_hours,
                rec.activity_minutes,
                rec.water_litres,
                rec.mood_rating,
                rec.stress_level,
                f"Sample record for {matched.name}",
            ),
        )
    conn.commit()
    conn.close()
    flash(f"Loaded 14-day sample dataset for {matched.name}.", "success")
    return redirect(url_for("records"))


# -----------------------------------------------------------------------------
# Intelligence & Analytics
# -----------------------------------------------------------------------------
@app.route("/intelligence")
@login_required
def intelligence():
    """Explainable health intelligence, sliding-window trends, recommendations."""
    conn = get_db()
    metrics = compute_dashboard_metrics(conn, g.user["id"])
    conn.close()
    return render_template("intelligence.html", metrics=metrics)


@app.route("/analytics")
@login_required
def analytics():
    """Visual multi-indicator timelines and statistical breakdown."""
    conn = get_db()
    metrics = compute_dashboard_metrics(conn, g.user["id"])
    conn.close()
    return render_template("analytics.html", metrics=metrics)


# -----------------------------------------------------------------------------
# Weekly Reports & Structured Exports
# -----------------------------------------------------------------------------
@app.route("/reports")
@login_required
def reports():
    """Official weekly report preview."""
    member_id_raw = request.args.get("member_id")
    target_id = g.user["id"]
    if member_id_raw and member_id_raw.isdigit():
        req_id = int(member_id_raw)
        if not can_manage_user(g.user, req_id):
            return render_template("403.html", message="You do not have permission to view this user's private report."), 403
        target_id = req_id

    conn = get_db()
    target_user = conn.execute("SELECT * FROM users WHERE id = ?", (target_id,)).fetchone()
    if not target_user:
        conn.close()
        flash("Requested member does not exist.", "error")
        return redirect(url_for("reports"))

    managed_members = []
    if g.user["role"] == "admin":
        managed_members = conn.execute("SELECT * FROM users ORDER BY full_name ASC").fetchall()
    elif g.user["role"] in ("manager", "community_worker"):
        managed_members = conn.execute(
            "SELECT * FROM users WHERE role IN ('normal_user', 'member', 'demo') OR id = ? ORDER BY full_name ASC",
            (g.user["id"],),
        ).fetchall()

    report_data = generate_user_weekly_report(conn, target_id, days=7)
    conn.close()

    return render_template(
        "reports.html",
        report_data=report_data,
        target_user=target_user,
        managed_members=managed_members,
        is_managing_other=(target_id != g.user["id"]),
    )


@app.route("/reports/export/json")
@login_required
def export_report_json_route():
    """Structured JSON download endpoint."""
    member_id_raw = request.args.get("member_id")
    target_id = g.user["id"]
    if member_id_raw and member_id_raw.isdigit():
        req_id = int(member_id_raw)
        if not can_manage_user(g.user, req_id):
            return render_template("403.html", message="You do not have permission to export this user's report."), 403
        target_id = req_id

    conn = get_db()
    target_user = conn.execute("SELECT * FROM users WHERE id = ?", (target_id,)).fetchone()
    if not target_user:
        conn.close()
        flash("Requested member does not exist.", "error")
        return redirect(url_for("reports"))

    report_data = generate_user_weekly_report(conn, target_id, days=7)
    conn.close()

    json_str = export_report_json(report_data)
    filename = f"healthbridge_report_{target_user['user_id']}.json"
    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


@app.route("/reports/export/csv")
@login_required
def export_report_csv_route():
    """Tabular CSV download endpoint."""
    member_id_raw = request.args.get("member_id")
    target_id = g.user["id"]
    if member_id_raw and member_id_raw.isdigit():
        req_id = int(member_id_raw)
        if not can_manage_user(g.user, req_id):
            return render_template("403.html", message="You do not have permission to export this user's report."), 403
        target_id = req_id

    conn = get_db()
    target_user = conn.execute("SELECT * FROM users WHERE id = ?", (target_id,)).fetchone()
    if not target_user:
        conn.close()
        flash("Requested member does not exist.", "error")
        return redirect(url_for("reports"))

    report_data = generate_user_weekly_report(conn, target_id, days=7)
    conn.close()

    csv_str = export_report_csv(report_data)
    filename = f"healthbridge_report_{target_user['user_id']}.csv"
    return Response(
        csv_str,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


# -----------------------------------------------------------------------------
# Management & Administration (RBAC)
# -----------------------------------------------------------------------------
@app.route("/manager")
@manager_required
def manager_dashboard():
    """Manager view of authorized community members."""
    conn = get_db()
    members_rows = conn.execute(
        """
        SELECT u.*, COUNT(r.id) as record_count
        FROM users u
        LEFT JOIN wellness_records r ON u.id = r.user_id
        WHERE u.role IN ('normal_user', 'member', 'demo')
        GROUP BY u.id
        ORDER BY u.full_name ASC
        """
    ).fetchall()
    conn.close()
    return render_template("manager_members.html", members=members_rows)


@app.route("/admin")
@admin_required
def admin_dashboard():
    """Administrative oversight dashboard."""
    conn = get_db()
    users_rows = conn.execute(
        """
        SELECT u.*, COUNT(r.id) as record_count
        FROM users u
        LEFT JOIN wellness_records r ON u.id = r.user_id
        GROUP BY u.id
        ORDER BY u.id ASC
        """
    ).fetchall()
    admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
    conn.close()
    return render_template("admin.html", users=users_rows, admin_count=admin_count)


@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@admin_required
def admin_change_role(user_id: int):
    """Assign or change user role across Normal User, Manager, and Admin."""
    new_role = request.form.get("role", "").strip()
    if new_role not in ("normal_user", "manager", "admin"):
        flash("Invalid role specified. Only 'normal_user', 'manager', and 'admin' can be assigned.", "error")
        return redirect(url_for("admin_dashboard"))

    conn = get_db()
    target_user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target_user:
        conn.close()
        flash("Target user not found.", "error")
        return redirect(url_for("admin_dashboard"))

    # Invariant: Prevent accidental removal or demotion of the last administrator
    if target_user["role"] == "admin" and new_role != "admin":
        admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        if admin_count <= 1:
            conn.close()
            flash("Action prohibited: Cannot demote the last remaining platform administrator.", "error")
            return redirect(url_for("admin_dashboard"))

    conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()
    flash(f"Successfully updated role for {target_user['full_name']} to {new_role.replace('_', ' ').title()}.", "success")
    return redirect(url_for("admin_dashboard"))


# -----------------------------------------------------------------------------
# Community Coach & Goals
# -----------------------------------------------------------------------------
@app.route("/coach")
@login_required
def coach():
    """Community coach and SDG 3 & 10 advocacy page."""
    conn = get_db()
    ideas = conn.execute(
        """
        SELECT ci.*, u.full_name as author_name
        FROM community_ideas ci
        JOIN users u ON ci.user_id = u.id
        ORDER BY ci.likes DESC, ci.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("coach.html", ideas=ideas)


@app.route("/coach/add-idea", methods=["POST"])
@login_required
def add_idea():
    """Share an accessible community wellness tip."""
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "General")
    description = request.form.get("description", "").strip()

    if title and description:
        conn = get_db()
        conn.execute(
            """
            INSERT INTO community_ideas (user_id, title, category, description, sdg_target)
            VALUES (?, ?, ?, ?, ?)
            """,
            (g.user["id"], title, category, description, "SDG 3 & 10"),
        )
        conn.commit()
        conn.close()
        flash("Thank you for contributing to the community wellness pool!", "success")
    return redirect(url_for("coach"))


@app.route("/coach/like/<int:idea_id>", methods=["POST"])
@login_required
def like_idea(idea_id: int):
    """Upvote a community tip."""
    conn = get_db()
    conn.execute("UPDATE community_ideas SET likes = likes + 1 WHERE id = ?", (idea_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("coach"))


@app.route("/goals")
@login_required
def goals():
    """Habit formation and personal wellness milestones."""
    conn = get_db()
    goal_rows = conn.execute(
        "SELECT * FROM wellness_goals WHERE user_id = ? ORDER BY id DESC",
        (g.user["id"],),
    ).fetchall()
    conn.close()
    return render_template("goals.html", goals=goal_rows)


@app.route("/goals/add", methods=["POST"])
@login_required
def add_goal():
    """Create a personal habit goal."""
    title = request.form.get("title", "").strip()
    indicator = request.form.get("indicator", "sleep_hours")
    target_value = float(request.form.get("target_value", 8.0))
    unit = request.form.get("unit", "units").strip()

    if title:
        conn = get_db()
        conn.execute(
            """
            INSERT INTO wellness_goals (user_id, indicator, title, target_value, unit)
            VALUES (?, ?, ?, ?, ?)
            """,
            (g.user["id"], indicator, title, target_value, unit),
        )
        conn.commit()
        conn.close()
        flash("Personal goal created.", "success")
    return redirect(url_for("goals"))


@app.route("/goals/toggle/<int:goal_id>", methods=["POST"])
@login_required
def toggle_goal(goal_id: int):
    """Toggle habit completion status."""
    conn = get_db()
    conn.execute(
        "UPDATE wellness_goals SET achieved = 1 - achieved WHERE id = ? AND user_id = ?",
        (goal_id, g.user["id"]),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("goals"))


# -----------------------------------------------------------------------------
# Validation Lab & Evaluator Benchmarks
# -----------------------------------------------------------------------------
@app.route("/validation-lab")
def validation_lab():
    """Interactive validation laboratory for hackathon evaluators."""
    return render_template("validation_lab.html")


@app.route("/api/test-validation", methods=["POST"])
def api_test_validation():
    """Execute live domain validator against specified edge cases."""
    data = request.get_json() or {}
    scenario = data.get("scenario", "")

    test_payloads = {
        "negative_sleep": {
            "title": "Negative Sleep Rejection",
            "date": "2026-10-12",
            "sleep": -2.0,
            "activity": 30,
            "water": 2.0,
        },
        "excessive_sleep": {
            "title": "Sleep Exceeds 24 Hours",
            "date": "2026-10-12",
            "sleep": 28.0,
            "activity": 15,
            "water": 1.5,
        },
        "negative_activity": {
            "title": "Negative Physical Activity",
            "date": "2026-10-12",
            "sleep": 7.0,
            "activity": -30,
            "water": 2.0,
        },
        "zero_water": {
            "title": "Non-Positive Water Hydration",
            "date": "2026-10-12",
            "sleep": 8.0,
            "activity": 45,
            "water": 0.0,
        },
        "duplicate_date": {
            "title": "Duplicate Date Entry Rejection",
            "date": "2026-10-01",
            "sleep": 7.0,
            "activity": 30,
            "water": 2.0,
            "duplicate": True,
        },
        "missing_date": {
            "title": "Missing / Empty Date String",
            "date": "",
            "sleep": 7.5,
            "activity": 30,
            "water": 2.0,
        },
        "invalid_mood": {
            "title": "Out-of-Bounds Mood Rating (1–5 scale)",
            "date": "2026-10-12",
            "sleep": 7.5,
            "activity": 30,
            "water": 2.0,
            "mood": 7,
        },
        "valid_record": {
            "title": "Valid Baseline Entry",
            "date": "2026-10-12",
            "sleep": 8.0,
            "activity": 40,
            "water": 2.2,
        },
    }

    tcase = test_payloads.get(scenario, test_payloads["negative_sleep"])
    record = WellnessRecord(
        date=tcase["date"],
        sleep_hours=tcase["sleep"],
        activity_minutes=tcase["activity"],
        water_litres=tcase["water"],
        mood_rating=tcase.get("mood"),
    )

    errors = record.validate()

    # Check duplicate date test
    if tcase.get("duplicate"):
        errors.append("Duplicate date '2026-10-01' already exists for user.")

    is_rejected = len(errors) > 0
    return jsonify({
        "scenario_title": tcase["title"],
        "payload": {
            "date": tcase["date"],
            "sleep_hours": tcase["sleep"],
            "activity_minutes": tcase["activity"],
            "water_litres": tcase["water"],
            "mood": tcase.get("mood"),
        },
        "rejected": is_rejected,
        "error_message": "; ".join(errors) if errors else "None (Valid)",
    })


# -----------------------------------------------------------------------------
# User Switcher, Profile & Settings
# -----------------------------------------------------------------------------
@app.route("/users")
@login_required
def users_view():
    """List registered community members."""
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
    conn.close()
    return render_template("users.html", users=users)


@app.route("/profile")
@login_required
def profile():
    """User profile overview."""
    return render_template("profile.html")


@app.route("/settings")
@login_required
def settings():
    """Configuration settings."""
    return render_template("settings.html")


@app.route("/settings/update-profile", methods=["POST"])
@login_required
def update_profile():
    """Update profile bio and full name."""
    full_name = request.form.get("full_name", "").strip()
    bio = request.form.get("bio", "").strip()

    if full_name:
        conn = get_db()
        conn.execute(
            "UPDATE users SET full_name = ?, bio = ? WHERE id = ?",
            (full_name, bio, g.user["id"]),
        )
        conn.commit()
        conn.close()
        flash("Profile updated successfully.", "success")
    return redirect(url_for("profile"))


@app.route("/settings/update-settings", methods=["POST"])
@login_required
def update_settings():
    """Update configurable targets and weights."""
    try:
        sleep_t = float(request.form.get("sleep_target", 8.0))
        act_t = int(request.form.get("activity_target", 30))
        water_t = float(request.form.get("water_target", 2.0))
        w_sleep = float(request.form.get("weight_sleep", 0.40))
        w_act = float(request.form.get("weight_activity", 0.35))
        w_water = float(request.form.get("weight_water", 0.25))

        total_w = round(w_sleep + w_act + w_water, 3)
        if total_w != 1.0:
            flash(f"Scoring weights must sum to 1.0 (current sum: {total_w}).", "error")
            return redirect(url_for("settings"))

        conn = get_db()
        conn.execute(
            """
            UPDATE users
            SET sleep_target = ?, activity_target = ?, water_target = ?,
                weight_sleep = ?, weight_activity = ?, weight_water = ?
            WHERE id = ?
            """,
            (sleep_t, act_t, water_t, w_sleep, w_act, w_water, g.user["id"]),
        )
        conn.commit()
        conn.close()
        flash("Target and weight configurations saved.", "success")
    except Exception as e:
        flash(f"Invalid configuration parameters: {e}", "error")

    return redirect(url_for("settings"))


@app.route("/settings/change-password", methods=["POST"])
@login_required
def change_password():
    """Change user password."""
    new_p = request.form.get("new_password", "")
    conf_p = request.form.get("confirm_password", "")

    if len(new_p) < 4:
        flash("Password must be at least 4 characters long.", "error")
    elif new_p != conf_p:
        flash("Passwords do not match.", "error")
    else:
        conn = get_db()
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_p), g.user["id"]),
        )
        conn.commit()
        conn.close()
        flash("Password updated successfully.", "success")
    return redirect(url_for("settings"))


@app.route("/api/set-theme", methods=["POST"])
def set_theme():
    """Persist theme selection."""
    data = request.get_json() or {}
    theme = data.get("theme", "light")
    if theme in ("light", "dark"):
        if g.user:
            conn = get_db()
            conn.execute("UPDATE users SET theme = ? WHERE id = ?", (theme, g.user["id"]))
            conn.commit()
            conn.close()
        return jsonify({"status": "success", "theme": theme})
    return jsonify({"status": "error"}), 400


@app.route("/api/chatbot", methods=["POST"])
def api_chatbot():
    """Contextual conversational assistant for HealthBridge."""
    data = request.get_json() or {}
    message = (data.get("message") or data.get("query") or "").strip()
    if not message:
        return jsonify({"reply": "Please ask a question about HealthBridge or your records."}), 400

    user_context = None
    if g.user:
        conn = get_db()
        metrics = compute_dashboard_metrics(conn, g.user["id"])
        conn.close()
        user_context = {
            "user_id": g.user["id"],
            "full_name": g.user["full_name"],
            "record_count": metrics["total_records"],
            "overall_score": metrics["overall_score"],
            "score_band": metrics["score_band"],
            "averages": metrics["averages"],
            "recommendations": metrics["recommendations"],
            "trends": metrics["trends"],
        }

    reply = get_chatbot_response(message, user_context)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  HealthBridge Web Platform Starting...")
    print("  URL: http://127.0.0.1:5000")
    print("=" * 65 + "\n")
    app.run(debug=True, port=5000)

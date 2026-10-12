"""
database.py — SQLite database management and persistence for HealthBridge.

Ensures seamless data persistence across web sessions while preserving
direct compatibility with the pure OOP domain models.
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash
from config import DATABASE_PATH, DEFAULT_TARGETS, DEFAULT_WEIGHTS
from data.sample_data import build_sample_users

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'normal_user' CHECK(role IN ('member', 'normal_user', 'manager', 'community_worker', 'admin', 'demo')),
    theme TEXT NOT NULL DEFAULT 'light' CHECK(theme IN ('light', 'dark')),
    bio TEXT DEFAULT '',
    sleep_target REAL NOT NULL DEFAULT 8.0,
    activity_target INTEGER NOT NULL DEFAULT 30,
    water_target REAL NOT NULL DEFAULT 2.0,
    weight_sleep REAL NOT NULL DEFAULT 0.40,
    weight_activity REAL NOT NULL DEFAULT 0.35,
    weight_water REAL NOT NULL DEFAULT 0.25,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wellness_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    record_date TEXT NOT NULL,
    sleep_hours REAL NOT NULL,
    activity_minutes INTEGER NOT NULL,
    water_litres REAL NOT NULL,
    mood_rating INTEGER,
    stress_level INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, record_date)
);

CREATE TABLE IF NOT EXISTS wellness_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    indicator TEXT NOT NULL,
    title TEXT NOT NULL,
    target_value REAL NOT NULL,
    unit TEXT NOT NULL,
    achieved INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS community_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    sdg_target TEXT NOT NULL DEFAULT 'SDG 3',
    likes INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""


def get_db(db_path: str | Path = DATABASE_PATH) -> sqlite3.Connection:
    """Connect to SQLite database with Row factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str | Path = DATABASE_PATH, force_reseed: bool = False) -> None:
    """Initialize database tables and seed sample data if empty or reseed required."""
    conn = get_db(db_path)
    with conn:
        conn.executescript(SCHEMA)

    # Clean up legacy test and persona accounts if present
    conn.execute(
        """
        DELETE FROM users WHERE user_id IN (
            'asha_sharma', 'rohan_patel', 'priya_nair', 'empty_test', 'admin_healthbridge'
        ) OR email IN (
            'asha@healthbridge.local', 'rohan@healthbridge.local', 'priya@healthbridge.local', 'empty_test@healthbridge.local'
        )
        """
    )
    conn.commit()

    # Check if database has users
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count < 3 or force_reseed:
        seed_database(conn)
    conn.close()


def seed_database(conn: sqlite3.Connection) -> None:
    """Seed sample users and their 14-day history into the database idempotently.

    Guarantees no duplicate records are created on re-initialization.
    """
    sample_users = build_sample_users()
    demo_sample = sample_users.get("trial_demo") or sample_users.get("demo")

    # Clean up legacy and old accounts to maintain a clean environment
    conn.execute(
        """
        DELETE FROM users WHERE user_id IN (
            'asha_sharma', 'rohan_patel', 'priya_nair', 'empty_test', 'admin_healthbridge', 'jivraj_singh'
        ) OR email IN (
            'asha@healthbridge.local', 'rohan@healthbridge.local', 'priya@healthbridge.local', 'empty_test@healthbridge.local', 'downlaygamer@gmail.com'
        )
        """
    )

    admin_password = "HBadmin#2026!"
    demo_password = "HBdemo#2026!"

    # Active accounts: Jivraj (Admin), Vaibhav (Admin), and Trial Demo
    user_meta = {
        "admin_jivraj": {
            "name": "Jivraj",
            "email": "admin@healthbridge.local",
            "role": "admin",
            "bio": "HealthBridge System Administrator & Lead Wellness Coordinator.",
            "password": admin_password,
        },
        "admin_vaibhav": {
            "name": "Vaibhav",
            "email": "vaibhav@healthbridge.local",
            "role": "admin",
            "bio": "HealthBridge System Administrator & Platform Governance Lead.",
            "password": admin_password,
        },
        "trial_demo": {
            "name": "Alex Rivera (Demo Profile)",
            "email": "demo@healthbridge.local",
            "role": "demo",
            "bio": "[DEMO DATA] Usable trial profile with realistic fictional lifestyle records for safe feature demonstration.",
            "password": demo_password,
        },
    }

    for user_slug, meta in user_meta.items():
        display_name = meta["name"]
        pwd_hash = generate_password_hash(meta["password"])

        conn.execute(
            """
            INSERT INTO users
            (user_id, full_name, email, password_hash, role, bio, sleep_target, activity_target, water_target)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                full_name = excluded.full_name,
                email = excluded.email,
                password_hash = excluded.password_hash,
                role = excluded.role,
                bio = excluded.bio,
                sleep_target = excluded.sleep_target,
                activity_target = excluded.activity_target,
                water_target = excluded.water_target
            """,
            (
                user_slug,
                display_name,
                meta["email"],
                pwd_hash,
                meta["role"],
                meta["bio"],
                DEFAULT_TARGETS["sleep_hours"],
                DEFAULT_TARGETS["activity_minutes"],
                DEFAULT_TARGETS["water_litres"],
            ),
        )

        user_row = conn.execute("SELECT id FROM users WHERE user_id = ?", (user_slug,)).fetchone()
        if not user_row:
            continue
        db_user_id = user_row["id"]

        # Clear existing records to ensure zero duplicate records when re-running initialization
        conn.execute("DELETE FROM wellness_records WHERE user_id = ?", (db_user_id,))

        # Populate with 14 days of realistic records
        if demo_sample and demo_sample.records:
            for rec in demo_sample.records:
                note_text = f"Sample record for {display_name}"
                if meta["role"] == "demo":
                    note_text = f"[Demo Data] {rec.date} habit log for trial showcase"
                elif meta["role"] == "admin":
                    note_text = f"Administrator activity log ({rec.date})"

                conn.execute(
                    """
                    INSERT INTO wellness_records
                    (user_id, record_date, sleep_hours, activity_minutes, water_litres, mood_rating, stress_level, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        db_user_id,
                        rec.date,
                        rec.sleep_hours,
                        rec.activity_minutes,
                        rec.water_litres,
                        rec.mood_rating,
                        rec.stress_level,
                        note_text,
                    ),
                )

        # Clear and insert default goals
        conn.execute("DELETE FROM wellness_goals WHERE user_id = ?", (db_user_id,))
        goals = [
            ("sleep_hours", "Consistent 7.5+ Hours Sleep", 7.5, "hours"),
            ("activity_minutes", "30 Minutes Active Movement", 30.0, "mins"),
            ("water_litres", "2.0 Litres Clean Water Intake", 2.0, "litres"),
        ]
        for indicator, title, target_val, unit in goals:
            conn.execute(
                """
                INSERT INTO wellness_goals
                (user_id, indicator, title, target_value, unit, achieved)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (db_user_id, indicator, title, target_val, unit, 0),
            )

    # Ensure community ideas foreign keys reference an active admin
    admin_id_row = conn.execute("SELECT id FROM users WHERE user_id = 'admin_jivraj'").fetchone()
    admin_db_id = admin_id_row["id"] if admin_id_row else 1
    conn.execute("UPDATE community_ideas SET user_id = ? WHERE user_id NOT IN (SELECT id FROM users)", (admin_db_id,))

    # Insert default community ideas if table is empty
    idea_count = conn.execute("SELECT COUNT(*) FROM community_ideas").fetchone()[0]
    if idea_count == 0:
        community_ideas = [
            (
                1,
                "10-Minute Desk Mobility Breaks",
                "Physical Activity",
                "Simple, zero-cost standing stretches every 90 minutes to reduce sedentary musculoskeletal tension.",
                "SDG 3.4 (NCD Prevention)",
                14,
            ),
            (
                2,
                "Community Hydration Cue System",
                "Hydration",
                "Fill a dedicated water flask every morning and place it in clear sight. Accessible tap water hydration for everyone.",
                "SDG 3 & 6 (Health & Clean Water)",
                22,
            ),
            (
                3,
                "Screen-Free Wind-Down Routine",
                "Sleep Hygiene",
                "Power down mobile screens 30 minutes before bedtime; read a paper book or practice quiet breathing for sleep onset.",
                "SDG 3 (Mental Well-Being)",
                19,
            ),
            (
                1,
                "Neighborhood Walking Circles",
                "Social Well-Being",
                "Free peer-led evening walks in neighborhood parks to reduce isolation and foster community inclusion.",
                "SDG 10 (Reduced Inequalities)",
                31,
            ),
        ]
        for _, title, cat, desc, sdg, likes in community_ideas:
            conn.execute(
                """
                INSERT OR IGNORE INTO community_ideas
                (user_id, title, category, description, sdg_target, likes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (admin_db_id, title, cat, desc, sdg, likes),
            )

    conn.commit()


def reset_development_database(db_path: str | Path = DATABASE_PATH) -> None:
    """Safely reset development database only and seed a clean demonstration environment.

    Verifies database is not production or external.
    Preserves schema and unrelated application data (community ideas).
    """
    path_str = str(db_path).lower()
    if "prod" in path_str or "http" in path_str:
        raise RuntimeError("Safety check failed: Refusing to reset production or external database.")

    conn = get_db(db_path)
    # 1. Preserve unrelated data (community ideas)
    try:
        ideas = conn.execute("SELECT * FROM community_ideas").fetchall()
        ideas_data = [dict(row) for row in ideas]
    except Exception:
        ideas_data = []

    # 2. Re-create user tables with updated CHECK constraint
    with conn:
        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.execute("DROP TABLE IF EXISTS wellness_records;")
        conn.execute("DROP TABLE IF EXISTS wellness_goals;")
        conn.execute("DROP TABLE IF EXISTS community_ideas;")
        conn.execute("DROP TABLE IF EXISTS users;")
        conn.executescript(SCHEMA)
        conn.execute("PRAGMA foreign_keys = ON;")

    # 3. Seed clean demonstration profiles and records first so foreign keys exist
    seed_database(conn)

    # 4. Restore preserved community ideas
    if ideas_data:
        # Get valid user IDs to ensure foreign key integrity
        valid_uids = [r[0] for r in conn.execute("SELECT id FROM users").fetchall()]
        fallback_uid = valid_uids[0] if valid_uids else 1
        with conn:
            for row in ideas_data:
                uid = row.get("user_id", fallback_uid)
                if uid not in valid_uids:
                    uid = fallback_uid
                conn.execute(
                    """
                    INSERT OR IGNORE INTO community_ideas
                    (id, user_id, title, category, description, sdg_target, likes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row.get("id"),
                        uid,
                        row.get("title", ""),
                        row.get("category", ""),
                        row.get("description", ""),
                        row.get("sdg_target", "SDG 3"),
                        row.get("likes", 0),
                        row.get("created_at"),
                    ),
                )

    conn.close()

"""
test_web.py — Automated test suite for HealthBridge Flask Web Interface.
"""

from __future__ import annotations
import unittest
from app import app
from models.database import init_db


class TestHealthBridgeWeb(unittest.TestCase):
    """Test web routes, sessions, exports, and validation API."""

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        init_db()

    def setUp(self):
        self.client = app.test_client()

    def login_demo(self):
        return self.client.post(
            "/login",
            data={"email": "demo@healthbridge.local", "password": "HBdemo#2026!"},
            follow_redirects=True,
        )

    def test_landing_page(self):
        """GET / should redirect unauthenticated users to the login page."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

        # Followed redirect should render login page
        followed = self.client.get("/", follow_redirects=True)
        self.assertEqual(followed.status_code, 200)
        self.assertIn(b"Sign in to your account", followed.data)

    def test_login_page(self):
        """GET /login should display sign-in form without any 1-click bypass buttons."""
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sign in to your account", response.data)
        self.assertNotIn(b"Try a Demo Account", response.data)
        self.assertNotIn(b"demo-login", response.data)

    def test_demo_login_redirect(self):
        """GET /demo-login/trial_demo should be blocked and redirect to login."""
        response = self.client.get("/demo-login/trial_demo", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Direct login without credentials is disabled", response.data)
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get("user_id"))

    def test_dashboard_authenticated(self):
        """Dashboard should render for authenticated user with metrics."""
        self.login_demo()
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Composite Wellness Score", response.data)
        self.assertIn(b"Non-Diagnostic Notice", response.data)

    def test_records_page(self):
        """Records page should display logged entries and validation bounds."""
        self.login_demo()
        response = self.client.get("/records")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Zero-Tolerance Validation Logic", response.data)

    def test_analytics_page(self):
        """Analytics page should render charts and statistical summary."""
        self.login_demo()
        response = self.client.get("/analytics")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Longitudinal Lifestyle Analysis", response.data)
        self.assertIn(b"Balance Wheel", response.data)

    def test_intelligence_page(self):
        """Intelligence page should display rule-based trends and recommendations."""
        self.login_demo()
        response = self.client.get("/intelligence")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sliding-Window Trend Classifications", response.data)
        self.assertIn(b"Personalized Non-Medical Recommendations", response.data)

    def test_reports_page(self):
        """Reports page should render the weekly summary."""
        self.login_demo()
        response = self.client.get("/reports")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Community Well-Being Weekly Report", response.data)
        self.assertIn(b"Mandatory Non-Diagnostic Disclaimer", response.data)

    def test_export_json(self):
        """Reports JSON export should return application/json with valid structure."""
        self.login_demo()
        response = self.client.get("/reports/export/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        self.assertIn(b"Alex Rivera", response.data)
        self.assertIn(b"disclaimer", response.data)

    def test_export_csv(self):
        """Reports CSV export should return text/csv with formatted rows."""
        self.login_demo()
        response = self.client.get("/reports/export/csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn(b"HealthBridge Weekly Wellness Report", response.data)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn(b"HealthBridge Weekly Wellness Report", response.data)

    def test_validation_lab_page(self):
        """Validation lab should be accessible."""
        response = self.client.get("/validation-lab")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Strict Domain Validation", response.data)

    def test_api_validation_rejection(self):
        """POST /api/test-validation with negative sleep should report rejected."""
        response = self.client.post(
            "/api/test-validation",
            json={"scenario": "negative_sleep"},
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["rejected"])
        self.assertIn("sleep_hours", json_data["error_message"])

    def test_api_validation_duplicate_date(self):
        """POST /api/test-validation with duplicate date should report rejected."""
        response = self.client.post(
            "/api/test-validation",
            json={"scenario": "duplicate_date"},
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["rejected"])
        self.assertIn("Duplicate date", json_data["error_message"])

    def test_api_chatbot_public(self):
        """POST /api/chatbot with general query should return project guidance."""
        response = self.client.post(
            "/api/chatbot",
            json={"message": "What is HealthBridge?"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("HealthBridge", data["reply"])

    def test_api_chatbot_authenticated(self):
        """POST /api/chatbot with score query for logged-in user should return personalized score."""
        self.login_demo()
        response = self.client.post(
            "/api/chatbot",
            json={"message": "What is my score?"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("Composite Wellness Score", data["reply"])
        self.assertIn("Sleep", data["reply"])

    def test_api_chatbot_empty(self):
        """POST /api/chatbot with empty query should return 400 error."""
        response = self.client.post(
            "/api/chatbot",
            json={"message": ""},
        )
        self.assertEqual(response.status_code, 400)

    def test_trial_demo_profile(self):
        """Trial demo user should authenticate with credentials, see demo banner, and access labeled demo records."""
        # Authenticate with credentials
        response = self.login_demo()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"DEMONSTRATION TRIAL PROFILE", response.data)
        self.assertIn(b"Alex Rivera", response.data)

        # Records page has demo records labeled
        rec_resp = self.client.get("/records")
        self.assertEqual(rec_resp.status_code, 200)
        self.assertIn(b"[Demo Data]", rec_resp.data)

        # Reports page generates safely
        rep_resp = self.client.get("/reports")
        self.assertEqual(rep_resp.status_code, 200)
        self.assertIn(b"Alex Rivera (Demo Profile)", rep_resp.data)

    def test_normal_user_isolation_and_rbac(self):
        """Normal users must never access other users' private records, reports, or management pages."""
        from models.database import get_db
        from werkzeug.security import generate_password_hash
        conn = get_db()
        conn.execute("DELETE FROM users WHERE user_id = 'test_normal_isolation'")
        conn.execute(
            """
            INSERT INTO users (user_id, email, password_hash, full_name, role)
            VALUES ('test_normal_isolation', 'normal_iso@healthbridge.local', ?, 'Normal Tester', 'normal_user')
            """,
            (generate_password_hash("HBiso#2026!"),),
        )
        conn.commit()
        normal_user = conn.execute("SELECT id FROM users WHERE user_id = 'test_normal_isolation'").fetchone()
        admin_user = conn.execute("SELECT id FROM users WHERE user_id = 'admin_jivraj'").fetchone()
        demo_user = conn.execute("SELECT id FROM users WHERE user_id = 'trial_demo'").fetchone()
        demo_rec = conn.execute("SELECT id FROM wellness_records WHERE user_id = ?", (demo_user["id"],)).fetchone()
        conn.close()

        try:
            # Authenticate as normal user
            self.client.post("/login", data={"email": "normal_iso@healthbridge.local", "password": "HBiso#2026!"})

            # Cannot view another user's records (HTTP 403)
            res = self.client.get(f"/records?member_id={demo_user['id']}")
            self.assertEqual(res.status_code, 403)
            self.assertIn(b"Access Restricted", res.data)

            # Cannot view another user's reports (HTTP 403)
            res = self.client.get(f"/reports?member_id={demo_user['id']}")
            self.assertEqual(res.status_code, 403)

            # Cannot export another user's report (HTTP 403)
            res = self.client.get(f"/reports/export/json?member_id={demo_user['id']}")
            self.assertEqual(res.status_code, 403)
            res = self.client.get(f"/reports/export/csv?member_id={demo_user['id']}")
            self.assertEqual(res.status_code, 403)

            # Cannot access manager or admin dashboards (HTTP 403)
            res = self.client.get("/admin")
            self.assertEqual(res.status_code, 403)
            res = self.client.get("/manager")
            self.assertEqual(res.status_code, 403)

            # Cannot delete another user's record (HTTP 403)
            if demo_rec:
                res = self.client.post(f"/records/delete/{demo_rec['id']}")
                self.assertEqual(res.status_code, 403)
        finally:
            conn = get_db()
            conn.execute("DELETE FROM users WHERE user_id = 'test_normal_isolation'")
            conn.commit()
            conn.close()

    def test_manager_permissions(self):
        """Managers can view authorized members' records and reports, but cannot access admin portal."""
        from models.database import get_db
        from werkzeug.security import generate_password_hash
        conn = get_db()
        conn.execute("DELETE FROM users WHERE user_id = 'test_manager_rbac'")
        conn.execute(
            """
            INSERT INTO users (user_id, email, password_hash, full_name, role)
            VALUES ('test_manager_rbac', 'manager_rbac@healthbridge.local', ?, 'Community Lead', 'manager')
            """,
            (generate_password_hash("HBmgr#2026!"),),
        )
        conn.commit()
        manager_user = conn.execute("SELECT id FROM users WHERE user_id = 'test_manager_rbac'").fetchone()
        demo_user = conn.execute("SELECT id FROM users WHERE user_id = 'trial_demo'").fetchone()
        admin_user = conn.execute("SELECT id FROM users WHERE user_id = 'admin_jivraj'").fetchone()
        conn.close()

        try:
            # Authenticate as manager
            self.client.post("/login", data={"email": "manager_rbac@healthbridge.local", "password": "HBmgr#2026!"})

            # Can access manager members portal
            res = self.client.get("/manager")
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Authorized Community Members", res.data)

            # Can view managed member records and reports
            res = self.client.get(f"/records?member_id={demo_user['id']}")
            self.assertEqual(res.status_code, 200)

            res = self.client.get(f"/reports?member_id={demo_user['id']}")
            self.assertEqual(res.status_code, 200)

            # CANNOT access admin dashboard (HTTP 403)
            res = self.client.get("/admin")
            self.assertEqual(res.status_code, 403)

            # CANNOT assign roles via admin endpoint (HTTP 403)
            res = self.client.post(f"/admin/users/{demo_user['id']}/role", data={"role": "admin"})
            self.assertEqual(res.status_code, 403)

            # CANNOT view administrator's private records or reports (HTTP 403)
            res = self.client.get(f"/records?member_id={admin_user['id']}")
            self.assertEqual(res.status_code, 403)
            res = self.client.get(f"/reports?member_id={admin_user['id']}")
            self.assertEqual(res.status_code, 403)
        finally:
            conn = get_db()
            conn.execute("DELETE FROM users WHERE user_id = 'test_manager_rbac'")
            conn.commit()
            conn.close()

    def test_admin_dashboard_and_role_management(self):
        """Admin can list users, assign any role, and system prevents demoting the last administrator."""
        from models.database import get_db
        from werkzeug.security import generate_password_hash

        conn = get_db()
        conn.execute("DELETE FROM users WHERE user_id = 'test_role_target'")
        conn.execute(
            """
            INSERT INTO users (user_id, email, password_hash, full_name, role)
            VALUES ('test_role_target', 'role_target@healthbridge.local', ?, 'Target Member', 'normal_user')
            """,
            (generate_password_hash("HBtarget#2026!"),),
        )
        conn.commit()
        target_user = conn.execute("SELECT id FROM users WHERE user_id = 'test_role_target'").fetchone()
        vaibhav = conn.execute("SELECT id FROM users WHERE user_id = 'admin_vaibhav'").fetchone()
        jivraj = conn.execute("SELECT id FROM users WHERE user_id = 'admin_jivraj'").fetchone()
        conn.close()

        try:
            # Authenticate as admin Jivraj
            self.client.post("/login", data={"email": "admin@healthbridge.local", "password": "HBadmin#2026!"})

            # Can access admin dashboard with users table
            res = self.client.get("/admin")
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"User &amp; Role Management", res.data)
            self.assertIn(b"All Platform Users", res.data)
            self.assertIn(b"Jivraj", res.data)
            self.assertIn(b"Vaibhav", res.data)

            # Can assign Manager role to Normal User
            res = self.client.post(
                f"/admin/users/{target_user['id']}/role",
                data={"role": "manager"},
                follow_redirects=True,
            )
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Successfully updated role", res.data)

            conn = get_db()
            updated_target = conn.execute("SELECT role FROM users WHERE id = ?", (target_user["id"],)).fetchone()
            self.assertEqual(updated_target["role"], "manager")

            # Can assign Admin role to User (Promote to Admin)
            res = self.client.post(
                f"/admin/users/{target_user['id']}/role",
                data={"role": "admin"},
                follow_redirects=True,
            )
            self.assertEqual(res.status_code, 200)
            updated_target2 = conn.execute("SELECT role FROM users WHERE id = ?", (target_user["id"],)).fetchone()
            self.assertEqual(updated_target2["role"], "admin")

            # Can assign Normal User role back
            res = self.client.post(
                f"/admin/users/{target_user['id']}/role",
                data={"role": "normal_user"},
                follow_redirects=True,
            )
            self.assertEqual(res.status_code, 200)
            updated_target3 = conn.execute("SELECT role FROM users WHERE id = ?", (target_user["id"],)).fetchone()
            self.assertEqual(updated_target3["role"], "normal_user")

            # Demote Vaibhav to normal_user leaving Jivraj as the sole admin
            res = self.client.post(
                f"/admin/users/{vaibhav['id']}/role",
                data={"role": "normal_user"},
                follow_redirects=True,
            )
            self.assertEqual(res.status_code, 200)

            # Safety Invariant: Demoting the last administrator (Jivraj) is prohibited
            res = self.client.post(
                f"/admin/users/{jivraj['id']}/role",
                data={"role": "normal_user"},
                follow_redirects=True,
            )
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Cannot demote the last remaining platform administrator", res.data)

            jivraj_check = conn.execute("SELECT role FROM users WHERE id = ?", (jivraj["id"],)).fetchone()
            self.assertEqual(jivraj_check["role"], "admin")

            # Restore Vaibhav back to admin
            conn.execute("UPDATE users SET role = 'admin' WHERE id = ?", (vaibhav["id"],))
            conn.commit()
            conn.close()
        finally:
            conn = get_db()
            conn.execute("DELETE FROM users WHERE user_id = 'test_role_target'")
            conn.commit()
            conn.close()

    def test_reports_empty_dataset_fix(self):
        """Zero-record users should render /reports safely without UndefinedError: summary."""
        # Create a new user with 0 records
        from models.database import get_db
        from werkzeug.security import generate_password_hash
        conn = get_db()
        conn.execute("DELETE FROM users WHERE email = 'empty_test@healthbridge.local'")
        conn.execute(
            """
            INSERT INTO users (user_id, email, password_hash, full_name, role)
            VALUES ('empty_test', 'empty_test@healthbridge.local', ?, 'Zero Record Tester', 'normal_user')
            """,
            (generate_password_hash("HBtest#2026!"),),
        )
        conn.commit()
        empty_user = conn.execute("SELECT id FROM users WHERE user_id = 'empty_test'").fetchone()
        conn.close()

        try:
            # Login as the zero-record user
            self.client.post("/login", data={"email": "empty_test@healthbridge.local", "password": "HBtest#2026!"})

            # GET /reports must succeed (HTTP 200) without throwing jinja2 UndefinedError
            res = self.client.get("/reports")
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Zero-Record State", res.data)
            self.assertIn(b"No records logged", res.data)
            self.assertIn(b"0.0", res.data)

            # Exports must succeed cleanly
            res_json = self.client.get("/reports/export/json")
            self.assertEqual(res_json.status_code, 200)
            self.assertIn(b"Zero Record Tester", res_json.data)

            res_csv = self.client.get("/reports/export/csv")
            self.assertEqual(res_csv.status_code, 200)
            self.assertIn(b"Zero Record Tester", res_csv.data)
        finally:
            # Clean up the test user so it never leaks into the active database
            conn = get_db()
            conn.execute("DELETE FROM users WHERE user_id = 'empty_test'")
            conn.commit()
            conn.close()

    def test_database_seeding_idempotency(self):
        """Rerunning init_db must not create duplicate users or duplicate records."""
        from models.database import init_db, get_db
        # Rerun initialization multiple times
        init_db()
        init_db()

        conn = get_db()
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        # Should have exactly 3 seeded accounts (Jivraj, Vaibhav, Demo)
        unique_uids = conn.execute("SELECT COUNT(DISTINCT user_id) FROM users").fetchone()[0]
        self.assertEqual(user_count, unique_uids)
        self.assertEqual(user_count, 3)

        # Check records for admin_jivraj are exactly 14, not 28 or 42
        jivraj = conn.execute("SELECT id FROM users WHERE user_id = 'admin_jivraj'").fetchone()
        rec_count = conn.execute("SELECT COUNT(*) FROM wellness_records WHERE user_id = ?", (jivraj["id"],)).fetchone()[0]
        self.assertEqual(rec_count, 14)
        conn.close()

    def test_account_switching_disabled_and_no_route(self):
        """Account switching route /users/switch is completely removed (returns 404)."""
        res = self.client.post("/users/switch", data={"user_id": 1, "password": "any"})
        self.assertEqual(res.status_code, 404)

    def test_login_requires_valid_credentials(self):
        """Users cannot log in without valid email/username and password."""
        # Wrong password rejected
        res_wrong = self.client.post(
            "/login",
            data={"email": "admin@healthbridge.local", "password": "WrongPassword!"},
            follow_redirects=True,
        )
        self.assertEqual(res_wrong.status_code, 200)
        self.assertIn(b"Invalid email address or password", res_wrong.data)
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get("user_id"))

        # Non-existent user rejected
        res_nonexistent = self.client.post(
            "/login",
            data={"email": "nobody@healthbridge.local", "password": "any"},
            follow_redirects=True,
        )
        self.assertEqual(res_nonexistent.status_code, 200)
        self.assertIn(b"Invalid email address or password", res_nonexistent.data)

        # Valid credentials succeeds
        res_ok = self.client.post(
            "/login",
            data={"email": "admin@healthbridge.local", "password": "HBadmin#2026!"},
            follow_redirects=True,
        )
        self.assertEqual(res_ok.status_code, 200)
        self.assertIn(b"Welcome back, Jivraj", res_ok.data)
        with self.client.session_transaction() as sess:
            self.assertIsNotNone(sess.get("user_id"))

    def test_demo_login_blocks_admin_and_other_bypass(self):
        """Calling /demo-login with admin or other keys is blocked and redirects to /login."""
        # Trying to bypass password for Jivraj
        res = self.client.get("/demo-login/admin", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Direct login without credentials is disabled", res.data)
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get("user_id"))

        # Trying to bypass password for Vaibhav
        res2 = self.client.get("/demo-login/vaibhav", follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        self.assertIn(b"Direct login without credentials is disabled", res2.data)
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get("user_id"))

    def test_users_view_has_no_switch_button_or_form(self):
        """The /users page displays members securely with NO switch button or switch forms."""
        self.login_demo()
        res = self.client.get("/users")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Community Members Directory", res.data)
        self.assertNotIn(b"Switch to", res.data)
        self.assertNotIn(b"Switch Account", res.data)
        self.assertNotIn(b"/users/switch", res.data)
        # Verify no switch buttons on user cards
        self.assertNotIn(b"Switch", res.data)


if __name__ == "__main__":
    unittest.main()

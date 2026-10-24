"""
Tests for Step 3: Login and Logout
Spec: .claude/specs/03-login-logout.md
"""

import pytest

import database.db as db_module
from app import app as flask_app
from database.db import create_user, init_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test_spendly.db"))
    flask_app.config.update({"TESTING": True, "SECRET_KEY": "test-secret"})
    with flask_app.app_context():
        init_db()
        create_user("Demo User", "Demo@Spendly.com", "demo123")
    return flask_app.test_client()


def _login(client, email="demo@spendly.com", password="demo123"):
    return client.post("/login", data={"email": email, "password": password})


def test_get_login_shows_form(client):
    res = client.get("/login")
    assert res.status_code == 200
    assert b'name="email"' in res.data
    assert b'name="password"' in res.data


def test_login_success_redirects_to_profile(client):
    res = _login(client)
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/profile")
    with client.session_transaction() as sess:
        assert sess["user_id"]


def test_login_email_case_and_spaces_insensitive(client):
    res = _login(client, email="  DEMO@spendly.COM ")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/profile")


def test_logged_in_user_redirected_from_login(client):
    _login(client)
    res = client.get("/login")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/profile")


def test_wrong_password_shows_error_without_session(client):
    res = _login(client, password="wrong-password")
    assert res.status_code == 200
    assert b"Invalid email or password." in res.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_unknown_email_same_error_as_wrong_password(client):
    res = _login(client, email="nobody@example.com")
    assert res.status_code == 200
    assert b"Invalid email or password." in res.data


@pytest.mark.parametrize(
    "email,password", [("", "demo123"), ("demo@spendly.com", ""), ("", "")]
)
def test_empty_field_shows_required_error(client, email, password):
    res = _login(client, email=email, password=password)
    assert res.status_code == 200
    assert b"All fields are required." in res.data


def test_failed_login_keeps_email_but_not_password(client):
    res = _login(client, email="demo@spendly.com", password="secret-guess")
    assert b'value="demo@spendly.com"' in res.data
    assert b"secret-guess" not in res.data


def test_logout_clears_session_and_redirects(client):
    _login(client)
    res = client.get("/logout", follow_redirects=True)
    assert res.status_code == 200
    assert b"You have been logged out." in res.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_profile_redirects_to_login_after_logout(client):
    _login(client)
    client.get("/logout")
    res = client.get("/profile")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/login")


def test_logout_when_not_logged_in_redirects_to_landing(client):
    res = client.get("/logout")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/")

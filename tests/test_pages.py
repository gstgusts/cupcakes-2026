from markupsafe import escape

from app import keycloak_admin
from app.models import User


# --- Home and login

def test_home_shows_sign_in_when_logged_out(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Sign in" in response.data


def test_home_redirects_to_profile_when_logged_in(client, login):
    login()
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile/")


def test_profile_requires_login(client):
    response = client.get("/profile/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# --- Profile

def test_profile_shows_seeded_user(client, login):
    # Emails are matched case-insensitively
    login(email="USER1@example.com")
    response = client.get("/profile/")
    assert response.status_code == 200
    assert b"user1@example.com" in response.data
    assert b"Edit profile" in response.data


def test_profile_missing(client, login):
    login(email="nobody@example.com")
    response = client.get("/profile/")
    assert response.status_code == 404
    assert b"No profile found for nobody@example.com" in response.data


def test_create_own_profile(app, client, login):
    login(email="new.profile@example.com")
    response = client.post("/profile/edit", data={"name": "New", "surname": "Profile"})
    assert response.status_code == 302

    with app.app_context():
        user = User.query.filter_by(email="new.profile@example.com").one()
        assert (user.name, user.surname) == ("New", "Profile")


def test_edit_profile_validation_error(client, login):
    login()
    response = client.post("/profile/edit", data={"name": "", "surname": "One"})
    assert response.status_code == 400
    assert b"First name is required." in response.data


# --- Users (admin only)

def test_users_list_forbidden_without_admin_role(client, login):
    login(roles=["user"])
    assert client.get("/users/").status_code == 403


def test_users_list_and_search(client, login):
    login(roles=["admin", "user"])

    response = client.get("/users/")
    assert response.status_code == 200
    assert b"user1@example.com" in response.data
    assert b"user2@example.com" in response.data

    response = client.get("/users/?q=user2")
    assert b"user2@example.com" in response.data
    assert b"user1@example.com" not in response.data


def test_create_user(app, client, login, monkeypatch):
    # Keycloak is not running in tests: replace the Admin API calls
    created = {}
    monkeypatch.setattr(keycloak_admin, "email_exists", lambda email: False)

    def fake_create_user(email, first_name, last_name, temporary_password):
        created.update(email=email, password=temporary_password)
        return "keycloak-id"

    monkeypatch.setattr(keycloak_admin, "create_user", fake_create_user)

    login(roles=["admin"])
    response = client.post("/users/new", data={"name": "Anna", "surname": "Berzina", "email": "Anna@Example.com"})

    assert response.status_code == 200
    assert b"User created" in response.data
    # The email is stored lowercase, and the shown password is the one sent to Keycloak
    assert created["email"] == "anna@example.com"
    # (HTML-escaped, since the password can contain "&")
    assert str(escape(created["password"])).encode() in response.data
    with app.app_context():
        assert User.query.filter_by(email="anna@example.com").count() == 1


def test_create_user_with_existing_email(client, login, monkeypatch):
    monkeypatch.setattr(keycloak_admin, "email_exists", lambda email: False)

    login(roles=["admin"])
    response = client.post("/users/new", data={"name": "User", "surname": "One", "email": "user1@example.com"})

    assert response.status_code == 400
    assert b"A user profile with this email already exists." in response.data

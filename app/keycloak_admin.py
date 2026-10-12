"""Small client for the Keycloak Admin REST API.

The app calls it as the service account of the cupcakes-web client (client credentials
grant). In keycloak/realm-cupcakes.json that account has only the realm-management roles
it needs: manage-users and view-users.
"""
import requests
from flask import current_app

TIMEOUT = 10  # seconds


class KeycloakError(Exception):
    """Keycloak is unreachable or rejected the request."""


class KeycloakConflict(KeycloakError):
    """A Keycloak user with the same username or email already exists."""


def _realm_url(path):
    c = current_app.config
    return f"{c['KEYCLOAK_INTERNAL_URL']}/realms/{c['KEYCLOAK_REALM']}{path}"


def _admin_url(path):
    c = current_app.config
    return f"{c['KEYCLOAK_INTERNAL_URL']}/admin/realms/{c['KEYCLOAK_REALM']}{path}"


def _access_token():
    c = current_app.config
    try:
        r = requests.post(
            _realm_url("/protocol/openid-connect/token"),
            data={
                "grant_type": "client_credentials",
                "client_id": c["KEYCLOAK_CLIENT_ID"],
                "client_secret": c["KEYCLOAK_CLIENT_SECRET"],
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        raise KeycloakError(f"Cannot get a Keycloak admin token: {e}") from e
    return r.json()["access_token"]


def _request(method, path, **kwargs):
    headers = {"Authorization": f"Bearer {_access_token()}"}
    try:
        return requests.request(method, _admin_url(path), headers=headers, timeout=TIMEOUT, **kwargs)
    except requests.RequestException as e:
        raise KeycloakError(f"Keycloak is not reachable: {e}") from e


def email_exists(email):
    """True if any Keycloak user in the realm has this email (case-insensitive)."""
    r = _request("GET", "/users", params={"email": email, "exact": "true"})
    if r.status_code != 200:
        raise KeycloakError(f"Keycloak user search failed ({r.status_code})")
    return len(r.json()) > 0


def create_user(email, first_name, last_name, temporary_password):
    """Creates an enabled user and returns its Keycloak id.

    The password is temporary, so Keycloak asks the user to set a new one at first login.
    The email is marked verified because an admin creates the account (there is no mail server).
    """
    payload = {
        "username": email,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": temporary_password, "temporary": True}],
    }
    r = _request("POST", "/users", json=payload)
    if r.status_code == 409:
        raise KeycloakConflict("A Keycloak user with this email already exists.")
    if r.status_code != 201:
        raise KeycloakError(f"Keycloak could not create the user ({r.status_code}): {r.text}")
    # The new user's URL is in the Location header: .../users/<id>
    return r.headers["Location"].rstrip("/").rsplit("/", 1)[-1]


def delete_user(user_id):
    r = _request("DELETE", f"/users/{user_id}")
    if r.status_code not in (204, 404):
        raise KeycloakError(f"Keycloak could not delete user {user_id} ({r.status_code})")

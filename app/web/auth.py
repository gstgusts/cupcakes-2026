from urllib.parse import urlencode

from authlib.integrations.base_client import OAuthError
from flask import Blueprint, current_app, redirect, render_template, session, url_for

from ..auth import oauth

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/login")
def login():
    return oauth.keycloak.authorize_redirect(url_for("auth.callback", _external=True))


@auth_bp.get("/callback")
def callback():
    try:
        # Exchanges the code for tokens and validates the ID token (signature, issuer, nonce)
        token = oauth.keycloak.authorize_access_token()
    except OAuthError as e:
        return render_template("home.html", error=f"Login failed: {e.description or e.error}"), 400

    claims = token["userinfo"]
    email = claims.get("email")
    if not email:
        return render_template("home.html", error="Your account has no email address."), 403
    # Users are linked by email, so only trust verified addresses
    if not claims.get("email_verified", False):
        return render_template("home.html", error="Your email address is not verified."), 403

    session.clear()
    session["user"] = {
        "sub": claims["sub"],
        "username": claims.get("preferred_username", ""),
        "name": claims.get("name", ""),
        "email": email,
        # Keycloak realm roles, mapped into the ID token as the "roles" claim
        "roles": claims.get("roles", []),
    }
    # Lets Keycloak end the session without asking for confirmation on logout
    session["id_token"] = token.get("id_token")
    return redirect(url_for("profile.details"))


@auth_bp.get("/logout")
def logout():
    id_token = session.get("id_token")
    session.clear()

    params = {
        "client_id": current_app.config["KEYCLOAK_CLIENT_ID"],
        "post_logout_redirect_uri": url_for("home", _external=True),
    }
    if id_token:
        params["id_token_hint"] = id_token
    end_session = oauth.keycloak.load_server_metadata()["end_session_endpoint"]
    return redirect(f"{end_session}?{urlencode(params)}")

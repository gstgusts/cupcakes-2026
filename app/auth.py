from functools import wraps

from authlib.integrations.flask_client import OAuth
from flask import redirect, session, url_for

oauth = OAuth()


def init_oauth(app):
    oauth.init_app(app)

    realm = app.config["KEYCLOAK_REALM"]
    issuer = f"{app.config['KEYCLOAK_PUBLIC_URL']}/realms/{realm}"
    public = f"{issuer}/protocol/openid-connect"
    internal = f"{app.config['KEYCLOAK_INTERNAL_URL']}/realms/{realm}/protocol/openid-connect"

    # Endpoints are set explicitly instead of via discovery: the browser reaches
    # Keycloak on localhost, while the app container reaches it by service name.
    oauth.register(
        name="keycloak",
        client_id=app.config["KEYCLOAK_CLIENT_ID"],
        client_secret=app.config["KEYCLOAK_CLIENT_SECRET"],
        authorize_url=f"{public}/auth",
        access_token_url=f"{internal}/token",
        client_kwargs={"scope": "openid email profile", "code_challenge_method": "S256"},
        # Provider metadata used to validate the ID token and to log out
        issuer=issuer,
        jwks_uri=f"{internal}/certs",
        end_session_endpoint=f"{public}/logout",
    )


def current_user():
    """Keycloak identity of the logged-in user, or None."""
    return session.get("user")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped

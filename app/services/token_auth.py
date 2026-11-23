"""Login for the JSON API: a Keycloak access token (React and Vue apps) or the Flask session (Flask pages).

The access token is a JWT signed by Keycloak. It is checked locally with the realm's public keys
(JWKS), so Keycloak is not called for every request.
"""
import time
from functools import wraps

import requests
from authlib.jose import JsonWebKey, JsonWebToken
from authlib.jose.errors import JoseError
from flask import current_app, g, jsonify, request

from .auth import current_user

# Keycloak signs access tokens with RS256
_jwt = JsonWebToken(["RS256"])

# Public keys of the realm, fetched once and kept for an hour
JWKS_MAX_AGE = 3600
_jwks_cache = {"keys": None, "fetched_at": 0.0}


class InvalidToken(Exception):
    """The Bearer token is missing parts, badly signed, expired or not meant for this API."""


def api_login_required(view):
    """Allows the request with a valid Bearer access token or a Flask session, otherwise 401 JSON.

    The identity (sub, username, email, roles, ...) is put into g.api_user.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if header:
            scheme, _, token = header.partition(" ")
            if scheme.lower() != "bearer" or not token:
                return _unauthorized("Use the header: Authorization: Bearer <access token>.")
            try:
                g.api_user = verify_access_token(token.strip())
            except InvalidToken as e:
                return _unauthorized(str(e))
        elif current_user() is not None:
            # The Flask pages call the API with the login session (cookie)
            g.api_user = current_user()
        else:
            return _unauthorized("Login required.")
        return view(*args, **kwargs)

    return wrapped


def verify_access_token(token):
    """Checks signature, issuer, expiry, type and client of a Keycloak access token; returns the identity."""
    config = current_app.config
    issuer = f"{config['KEYCLOAK_PUBLIC_URL']}/realms/{config['KEYCLOAK_REALM']}"
    claims_options = {
        "iss": {"essential": True, "value": issuer},
        "exp": {"essential": True},
        # Keycloak marks access tokens with typ "Bearer" (an ID token has "ID")
        "typ": {"essential": True, "value": "Bearer"},
        # azp: the client the token was issued to
        "azp": {"essential": True, "value": config["KEYCLOAK_SPA_CLIENT_ID"]},
    }
    try:
        claims = _decode(token, claims_options)
    except JoseError as e:
        raise InvalidToken(f"Invalid access token: {e.description or e.error}.") from e
    except ValueError as e:
        # Unknown key id even after fetching the keys again, or a malformed token
        raise InvalidToken(f"Invalid access token: {e}.") from e

    return {
        "sub": claims["sub"],
        "username": claims.get("preferred_username", ""),
        "name": claims.get("name", ""),
        "first_name": claims.get("given_name", ""),
        "last_name": claims.get("family_name", ""),
        "email": claims.get("email", ""),
        "roles": claims.get("roles", []),
    }


def _decode(token, claims_options):
    try:
        claims = _jwt.decode(token, _public_keys(), claims_options=claims_options)
    except ValueError:
        # Keycloak may have rotated its keys: fetch them again once and retry
        claims = _jwt.decode(token, _public_keys(refresh=True), claims_options=claims_options)
    # Checks iss, exp, typ and azp (decode only checks the signature)
    claims.validate(leeway=10)
    return claims


def _public_keys(refresh=False):
    """The realm's JWKS, fetched over the internal Keycloak URL and cached."""
    expired = time.monotonic() - _jwks_cache["fetched_at"] > JWKS_MAX_AGE
    if refresh or expired or _jwks_cache["keys"] is None:
        config = current_app.config
        url = f"{config['KEYCLOAK_INTERNAL_URL']}/realms/{config['KEYCLOAK_REALM']}/protocol/openid-connect/certs"
        _jwks_cache["keys"] = JsonWebKey.import_key_set(fetch_jwks(url))
        _jwks_cache["fetched_at"] = time.monotonic()
    return _jwks_cache["keys"]


def fetch_jwks(url):
    """Downloads the JWKS document (replaced in tests)."""
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()


def _unauthorized(message):
    response = jsonify(error=message)
    response.status_code = 401
    # Tells the client which login scheme the API expects
    response.headers["WWW-Authenticate"] = 'Bearer realm="cupcakes"'
    return response

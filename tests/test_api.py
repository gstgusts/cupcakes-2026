import time
import uuid
from datetime import date
from decimal import Decimal

import pytest
from authlib.jose import JsonWebKey, JsonWebToken

from app import db
from app.models import Cupcake, CupcakeType, Prediction, PredictionModel, Store
from app.services import token_auth

ISSUER = "http://localhost:8080/realms/cupcakes"

# Test signing keys: "keycloak" plays Keycloak's realm key, "other" is a key Keycloak never published
KEYCLOAK_KEY = JsonWebKey.generate_key("RSA", 2048, is_private=True, options={"kid": "keycloak-key"})
OTHER_KEY = JsonWebKey.generate_key("RSA", 2048, is_private=True, options={"kid": "keycloak-key"})
_jwt = JsonWebToken(["RS256"])


@pytest.fixture(autouse=True)
def fake_keycloak_keys(monkeypatch):
    """Keycloak is not running in tests: the JWKS download returns the test key. Counts the downloads."""
    calls = []

    def fetch_jwks(url):
        calls.append(url)
        return {"keys": [KEYCLOAK_KEY.as_dict(is_private=False)]}

    monkeypatch.setattr(token_auth, "fetch_jwks", fetch_jwks)
    monkeypatch.setattr(token_auth, "_jwks_cache", {"keys": None, "fetched_at": 0.0})
    return calls


def make_token(key=KEYCLOAK_KEY, **changes):
    """An access token like Keycloak issues for the cupcakes-spa client."""
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "sub": "user1-sub",
        "typ": "Bearer",
        "azp": "cupcakes-spa",
        "iat": now,
        "exp": now + 300,
        "preferred_username": "user1",
        "email": "user1@example.com",
        "roles": ["admin", "user"],
    } | changes
    return _jwt.encode({"alg": "RS256", "kid": key.kid}, claims, key).decode()


def bearer(token=None):
    return {"Authorization": f"Bearer {token or make_token()}"}


@pytest.fixture
def model_id(app):
    """A new cupcake with a Case 3 prediction model at Riga Centre (d = 150, σ = 30, c = 10, p = 15, s = 2)."""
    with app.app_context():
        # Queries first: they flush the session, which must not happen with half-built objects
        cupcake_type = CupcakeType.query.filter_by(name="Classic").one()
        store = Store.query.filter_by(name="Riga Centre").one()
        cupcake = Cupcake(name=f"API Cupcake {uuid.uuid4().hex[:8]}", cupcake_type=cupcake_type)
        model = PredictionModel(name="Case 3", cupcake=cupcake, store=store,
                                average_demand=150, demand_std_dev=30, production_cost=Decimal("10"),
                                selling_price=Decimal("15"), salvage_value=Decimal("2"))
        db.session.add(model)
        db.session.commit()
        return model.id


def _post(client, model_id, day="2027-01-15", **kwargs):
    kwargs.setdefault("headers", bearer())
    return client.post("/api/predictions", json={"prediction_model_id": str(model_id), "date": day}, **kwargs)


# --- Login

@pytest.mark.parametrize("method, url", [
    ("get", "/api/prediction-models"),
    ("get", "/api/predictions"),
    ("post", "/api/predictions"),
])
def test_endpoints_require_login(client, method, url):
    response = getattr(client, method)(url)
    assert response.status_code == 401
    assert response.is_json
    assert response.json == {"error": "Login required."}
    assert response.headers["WWW-Authenticate"].startswith("Bearer")


def test_bearer_token_is_accepted(client):
    response = client.get("/api/predictions", headers=bearer())
    assert response.status_code == 200
    assert response.is_json


def test_flask_session_is_accepted(client, login):
    # The Flask pages call the API with their login session
    login()
    assert client.get("/api/predictions").status_code == 200


@pytest.mark.parametrize("token", [
    make_token(exp=int(time.time()) - 60),                   # expired
    make_token(iss="http://evil.example/realms/cupcakes"),   # another issuer
    make_token(azp="cupcakes-web"),                          # issued to another client
    make_token(typ="ID"),                                    # an ID token, not an access token
    make_token(key=OTHER_KEY),                               # signed with a key Keycloak never published
    "not-a-jwt",
])
def test_invalid_tokens_are_rejected(client, token):
    response = client.get("/api/predictions", headers=bearer(token))
    assert response.status_code == 401
    assert response.json["error"].startswith("Invalid access token")


def test_authorization_header_must_be_bearer(client):
    response = client.get("/api/predictions", headers={"Authorization": "Basic dXNlcjE6cGFzc3dvcmQ="})
    assert response.status_code == 401


def test_public_keys_are_fetched_once(client, fake_keycloak_keys):
    for _ in range(3):
        assert client.get("/api/predictions", headers=bearer()).status_code == 200
    assert len(fake_keycloak_keys) == 1
    assert fake_keycloak_keys[0].endswith("/realms/cupcakes/protocol/openid-connect/certs")


def test_unknown_key_id_fetches_keys_again(client, fake_keycloak_keys):
    # Keycloak rotated its key: the cached keys do not know the new kid, so they are fetched once more
    client.get("/api/predictions", headers=bearer())
    response = client.get("/api/predictions", headers=bearer(make_token(key=_with_kid(OTHER_KEY, "new-key"))))
    assert response.status_code == 401
    assert len(fake_keycloak_keys) == 2


def _with_kid(key, kid):
    return JsonWebKey.import_key(key.as_dict(is_private=True) | {"kid": kid})


# --- GET /api/prediction-models

def test_prediction_models(client, model_id):
    response = client.get("/api/prediction-models", headers=bearer())
    assert response.status_code == 200
    model = next(m for m in response.json if m["id"] == str(model_id))
    assert model["name"] == "Case 3"
    assert model["store"]["name"] == "Riga Centre"
    assert model["cupcake"]["name"].startswith("API Cupcake")
    assert (model["average_demand"], model["demand_std_dev"]) == (150, 30)
    assert (model["production_cost"], model["selling_price"], model["salvage_value"]) == (10, 15, 2)
    assert model["critical_ratio"] == pytest.approx(5 / 13)


# --- GET /api/predictions

def test_predictions_newest_date_first(app, client, model_id):
    with app.app_context():
        for day in (date(2027, 2, 1), date(2027, 2, 3), date(2027, 2, 2)):
            db.session.add(Prediction(prediction_model_id=model_id, date=day, recommended_quantity=141))
        db.session.commit()

    response = client.get("/api/predictions", headers=bearer())
    dates = [p["date"] for p in response.json if p["prediction_model"]["id"] == str(model_id)]
    assert dates == ["2027-02-03", "2027-02-02", "2027-02-01"]
    first = response.json[0]
    assert set(first) == {"id", "date", "recommended_quantity", "prediction_model", "cupcake", "store", "created_at"}


# --- POST /api/predictions

def test_create_prediction(app, client, model_id):
    response = _post(client, model_id)
    assert response.status_code == 201
    assert response.json["recommended_quantity"] == 141
    assert response.json["date"] == "2027-01-15"
    assert response.json["prediction_model"]["id"] == str(model_id)
    assert response.headers["Location"] == f"/predictions/{response.json['id']}"
    with app.app_context():
        assert db.session.get(Prediction, uuid.UUID(response.json["id"])).recommended_quantity == 141


def test_create_prediction_with_session(client, login, model_id):
    login()
    assert _post(client, model_id, headers={}).status_code == 201


def test_create_prediction_duplicate(client, model_id):
    _post(client, model_id)
    response = _post(client, model_id)
    assert response.status_code == 409
    assert response.json == {"errors": {"date": "This model already has a prediction for this date."}}


MODEL = "the test model"  # replaced by the id of the model_id fixture


@pytest.mark.parametrize("body, errors", [
    ({}, {"prediction_model_id": "Choose a prediction model.", "date": "Date is required."}),
    ({"prediction_model_id": "not-a-uuid", "date": "2027-01-15"}, {"prediction_model_id": "Choose a prediction model."}),
    ({"prediction_model_id": str(uuid.uuid4()), "date": "2027-01-15"}, {"prediction_model_id": "Choose a prediction model."}),
    ({"prediction_model_id": MODEL, "date": "2027-02-30"}, {"date": "Enter a valid date."}),
    ({"prediction_model_id": MODEL, "date": 20270115}, {"date": "Date is required."}),
])
def test_create_prediction_validation_errors(client, model_id, body, errors):
    body = {key: str(model_id) if value == MODEL else value for key, value in body.items()}
    response = client.post("/api/predictions", json=body, headers=bearer())
    assert response.status_code == 400
    assert response.json == {"errors": errors}


@pytest.mark.parametrize("kwargs", [
    {"data": "prediction_model_id=x&date=2027-01-15", "content_type": "application/x-www-form-urlencoded"},
    {"data": "[1, 2]", "content_type": "application/json"},
    {"data": "{not json", "content_type": "application/json"},
])
def test_create_prediction_requires_json_object(client, kwargs):
    response = client.post("/api/predictions", headers=bearer(), **kwargs)
    assert response.status_code == 400
    assert "request" in response.json["errors"]


def test_unknown_api_url_returns_json(client):
    response = client.get("/api/nothing-here", headers=bearer())
    assert response.status_code == 404
    assert response.json == {"error": "Not found."}


def test_unknown_page_still_returns_html(client):
    response = client.get("/nothing-here")
    assert response.status_code == 404
    assert not response.is_json


def test_wrong_method_returns_json(client):
    response = client.delete("/api/predictions", headers=bearer())
    assert response.status_code == 405
    assert response.json == {"error": "Method not allowed."}

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app import db
from app.models import Cupcake, CupcakeType, Prediction, PredictionModel, Store


@pytest.fixture
def model_id(app):
    """A new cupcake with a Case 3 prediction model at Riga Centre (d = 150, σ = 30, c = 10, p = 15, s = 2)."""
    with app.app_context():
        # Queries first: they flush the session, which must not happen with half-built objects
        cupcake_type = CupcakeType.query.filter_by(name="Classic").one()
        store = Store.query.filter_by(name="Riga Centre").one()
        cupcake = Cupcake(name=f"Predicted Cupcake {uuid.uuid4().hex[:8]}", cupcake_type=cupcake_type)
        model = PredictionModel(name="Case 3", cupcake=cupcake, store=store,
                                average_demand=150, demand_std_dev=30, production_cost=Decimal("10"),
                                selling_price=Decimal("15"), salvage_value=Decimal("2"))
        db.session.add(model)
        db.session.commit()
        return model.id


def _create(client, model_id, day="2026-12-01", **kwargs):
    return client.post("/predictions/new", data={"model": str(model_id), "date": day}, **kwargs)


def test_pages_require_login(client):
    for url in ("/predictions/", "/predictions/new", f"/predictions/{uuid.uuid4()}"):
        response = client.get(url)
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]


def test_new_form_defaults(client, login, model_id):
    login(roles=["user"])
    response = client.get(f"/predictions/new?model={model_id}")
    assert response.status_code == 200
    # The model from the link is selected, and the date is tomorrow
    assert f'value="{model_id}" selected'.encode() in response.data
    assert f'value="{(date.today() + timedelta(days=1)).isoformat()}"'.encode() in response.data


def test_create_prediction(app, client, login, model_id):
    # Any logged-in user can create predictions
    login(roles=["user"])
    response = _create(client, model_id)

    assert response.status_code == 302
    with app.app_context():
        prediction = Prediction.query.filter_by(prediction_model_id=model_id).one()
        assert prediction.date == date(2026, 12, 1)
        assert prediction.recommended_quantity == 141
    assert response.headers["Location"] == f"/predictions/{prediction.id}"


def test_result_page_shows_quantity_and_steps(client, login, model_id):
    login()
    response = _create(client, model_id, follow_redirects=True)
    assert b"Prediction created." in response.data
    assert b">141<" in response.data
    # CR, z and the exact quantity
    assert b"0.3846" in response.data
    assert b"-0.2934" in response.data
    assert b"141.20" in response.data
    assert b"so bake fewer than the average demand" in response.data


def test_list_shows_predictions(client, login, model_id):
    login()
    _create(client, model_id, day="2026-12-24")
    response = client.get("/predictions/")
    assert b"2026-12-24" in response.data
    assert b">141<" in response.data


def test_one_prediction_per_model_and_date(app, client, login, model_id):
    login()
    _create(client, model_id)
    response = _create(client, model_id)
    assert response.status_code == 400
    assert b"This model already has a prediction for this date." in response.data
    # Links to the existing prediction
    with app.app_context():
        existing = Prediction.query.filter_by(prediction_model_id=model_id).one()
    assert f"/predictions/{existing.id}".encode() in response.data


@pytest.mark.parametrize("data, message", [
    ({"model": "", "date": "2026-12-01"}, b"Choose a prediction model."),
    ({"model": str(uuid.uuid4()), "date": "2026-12-01"}, b"Choose a prediction model."),
    ({"date": ""}, b"Date is required."),
    ({"date": "2026-02-30"}, b"Enter a valid date."),
])
def test_create_prediction_invalid(client, login, model_id, data, message):
    login()
    response = client.post("/predictions/new", data={"model": str(model_id)} | data)
    assert response.status_code == 400
    assert message in response.data


def test_unknown_prediction(client, login):
    login()
    assert client.get(f"/predictions/{uuid.uuid4()}").status_code == 404


def test_model_with_predictions_cannot_be_deleted(app, client, login, model_id):
    login(roles=["admin"])
    _create(client, model_id)
    response = client.post(f"/prediction-models/{model_id}/delete", follow_redirects=True)
    assert b"has predictions and cannot be deleted." in response.data
    assert b"alert-error" in response.data
    with app.app_context():
        assert db.session.get(PredictionModel, model_id) is not None


def test_prediction_models_list_links_to_new_prediction(client, login, model_id):
    login(roles=["user"])
    assert f'href="/predictions/new?model={model_id}"'.encode() in client.get("/prediction-models/").data


def test_nav_shows_predictions_link(client, login):
    login()
    assert b'href="/predictions/"' in client.get("/profile/").data

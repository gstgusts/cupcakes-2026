import uuid
from datetime import date
from decimal import Decimal

import pytest

from app import db
from app.models import Cupcake, CupcakeType, Plan, Prediction, PredictionModel, Store, User

DAY = date(2026, 12, 1)


def _add_prediction(cupcake, store, model_name, quantity, day=DAY):
    model = PredictionModel(name=model_name, cupcake=cupcake, store=store,
                            average_demand=150, demand_std_dev=30, production_cost=Decimal("10"),
                            selling_price=Decimal("15"), salvage_value=Decimal("2"))
    prediction = Prediction(prediction_model=model, date=day, recommended_quantity=quantity)
    db.session.add(prediction)
    return prediction


@pytest.fixture
def ids(app):
    """A new cupcake at Riga Centre with predictions from two models for the same date."""
    with app.app_context():
        # Queries first: they flush the session, which must not happen with half-built objects
        cupcake_type = CupcakeType.query.filter_by(name="Classic").one()
        store = Store.query.filter_by(name="Riga Centre").one()
        cupcake = Cupcake(name=f"Planned Cupcake {uuid.uuid4().hex[:8]}", cupcake_type=cupcake_type)
        first = _add_prediction(cupcake, store, "Case 3", 141)
        second = _add_prediction(cupcake, store, "Weekend", 160)
        db.session.commit()
        return {"cupcake": cupcake.id, "store": store.id, "prediction": first.id, "other_prediction": second.id}


def _confirm(client, prediction_id, quantity="141", **kwargs):
    return client.post("/plans/new", data={"prediction": str(prediction_id), "quantity": quantity}, **kwargs)


def test_list_requires_login(client):
    response = client.get("/plans/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_prediction_page_shows_confirm_form(client, login, ids):
    login()
    response = client.get(f"/predictions/{ids['prediction']}")
    assert b"Confirm plan" in response.data
    # The recommended quantity is the default
    assert b'value="141"' in response.data


def test_confirm_plan(app, client, login, ids):
    # Any logged-in user with a profile can confirm (user1 has one)
    login(email="user1@example.com", roles=["user"])
    response = _confirm(client, ids["prediction"], quantity=" 135 ")

    assert response.status_code == 302
    assert response.headers["Location"] == "/plans/"
    with app.app_context():
        plan = Plan.query.filter_by(prediction_id=ids["prediction"]).one()
        assert plan.quantity_confirmed == 135
        # Cupcake, store and date come from the prediction
        assert (plan.cupcake_id, plan.store_id, plan.date) == (ids["cupcake"], ids["store"], DAY)
        assert plan.confirmed_by.email == "user1@example.com"
        assert plan.confirmed_at is not None


def test_plans_list(client, login, ids):
    login()
    response = _confirm(client, ids["prediction"], quantity="135", follow_redirects=True)
    assert b"Plan confirmed: bake 135 cupcakes." in response.data
    assert b"2026-12-01" in response.data
    assert b">141<" in response.data  # recommended
    assert b">135<" in response.data  # confirmed
    assert b"User One" in response.data


def test_prediction_page_shows_confirmed_plan(client, login, ids):
    login()
    _confirm(client, ids["prediction"], quantity="135")
    response = client.get(f"/predictions/{ids['prediction']}")
    assert b"Confirm plan" not in response.data
    assert b"Confirmed: bake" in response.data
    assert b"By User One" in response.data


def test_one_plan_per_cupcake_store_and_date(app, client, login, ids):
    login()
    _confirm(client, ids["prediction"])
    # The other model's prediction is for the same cupcake, store and date
    page = client.get(f"/predictions/{ids['other_prediction']}")
    assert b"Confirm plan" not in page.data
    assert b'based on the prediction of model "Case 3"' in page.data

    response = _confirm(client, ids["other_prediction"], quantity="160")
    assert response.status_code == 409
    assert b"A plan for this cupcake, store and date is already confirmed." in response.data
    with app.app_context():
        assert Plan.query.filter_by(cupcake_id=ids["cupcake"]).count() == 1


@pytest.mark.parametrize("quantity, message", [
    ("", b"Quantity is required."),
    ("abc", b"Enter a whole number of cupcakes, 0 or more."),
    ("-5", b"Enter a whole number of cupcakes, 0 or more."),
    ("1.5", b"Enter a whole number of cupcakes, 0 or more."),
    ("100001", b"Quantity can be at most 100000."),
])
def test_confirm_plan_invalid_quantity(app, client, login, ids, quantity, message):
    login()
    response = _confirm(client, ids["prediction"], quantity=quantity)
    assert response.status_code == 400
    assert message in response.data
    # The prediction page is shown again with the typed value
    assert b"Bake" in response.data
    assert f'value="{quantity}"'.encode() in response.data
    with app.app_context():
        assert Plan.query.filter_by(prediction_id=ids["prediction"]).count() == 0


def test_confirm_plan_requires_profile(app, client, login, ids):
    # user3 has a Keycloak account but no profile in our database
    login(email="user3@example.com")
    response = _confirm(client, ids["prediction"])
    assert response.status_code == 403
    assert b"Create your profile before confirming plans." in response.data
    with app.app_context():
        assert User.find_by_email("user3@example.com") is None
        assert Plan.query.filter_by(prediction_id=ids["prediction"]).count() == 0


@pytest.mark.parametrize("prediction", ["", "not-a-uuid", str(uuid.uuid4())])
def test_confirm_plan_unknown_prediction(client, login, prediction):
    login()
    assert client.post("/plans/new", data={"prediction": prediction, "quantity": "10"}).status_code == 404


def test_confirm_plan_requires_login(client, ids):
    response = _confirm(client, ids["prediction"])
    assert response.status_code == 302


def test_nav_shows_plans_link(client, login):
    login()
    assert b'href="/plans/"' in client.get("/profile/").data

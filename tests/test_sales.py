import re
import uuid
from datetime import date
from decimal import Decimal

import pytest

from app import db
from app.models import Cupcake, CupcakeType, Plan, Prediction, PredictionModel, Sales, Store, User

DAY = date(2026, 12, 2)


@pytest.fixture
def plan_id(app):
    """A confirmed plan to bake 135 cupcakes (Case 3 model, selling price 15) at Riga Centre."""
    with app.app_context():
        # Queries first: they flush the session, which must not happen with half-built objects
        cupcake_type = CupcakeType.query.filter_by(name="Classic").one()
        store = Store.query.filter_by(name="Riga Centre").one()
        user = User.find_by_email("user1@example.com")
        cupcake = Cupcake(name=f"Sold Cupcake {uuid.uuid4().hex[:8]}", cupcake_type=cupcake_type)
        model = PredictionModel(name="Case 3", cupcake=cupcake, store=store,
                                average_demand=150, demand_std_dev=30, production_cost=Decimal("10"),
                                selling_price=Decimal("15"), salvage_value=Decimal("2"))
        prediction = Prediction(prediction_model=model, date=DAY, recommended_quantity=141)
        plan = Plan(date=DAY, cupcake=cupcake, store=store, prediction=prediction,
                    quantity_confirmed=135, confirmed_by=user)
        db.session.add(plan)
        db.session.commit()
        return plan.id


def _record(client, plan_id, quantity_sold="120", revenue="1800", **kwargs):
    return client.post(f"/sales/new?plan={plan_id}",
                       data={"quantity_sold": quantity_sold, "revenue": revenue}, **kwargs)


def test_pages_require_login(client, plan_id):
    for url in ("/sales/", f"/sales/new?plan={plan_id}"):
        response = client.get(url)
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]


def test_plans_list_links_to_record_sales(client, login, plan_id):
    login()
    assert f'href="/sales/new?plan={plan_id}"'.encode() in client.get("/plans/").data


def test_new_form_shows_plan(client, login, plan_id):
    login()
    response = client.get(f"/sales/new?plan={plan_id}")
    assert response.status_code == 200
    assert b"2026-12-02" in response.data
    assert b"135</span> cupcakes baked" in response.data
    assert b"15.00 per cupcake" in response.data


def test_record_sales(app, client, login, plan_id):
    login(roles=["user"])
    # Decimal comma is accepted
    response = _record(client, plan_id, quantity_sold=" 120 ", revenue="1750,50")

    assert response.status_code == 302
    assert response.headers["Location"] == "/sales/"
    with app.app_context():
        sales = Sales.query.filter_by(plan_id=plan_id).one()
        assert sales.quantity_sold == 120
        assert sales.revenue == Decimal("1750.50")
        # The date comes from the plan
        assert sales.date == DAY
        assert sales.recorded_at is not None


def test_sales_list_with_left_over_and_totals(client, login, plan_id):
    login()
    response = _record(client, plan_id, quantity_sold="120", revenue="1800", follow_redirects=True)
    assert b"Sales recorded: 120 cupcakes sold." in response.data
    assert b"2026-12-02" in response.data
    assert b">135<" in response.data      # baked
    assert b">120<" in response.data      # sold
    assert b">15<" in response.data       # left over
    assert b">1800.00<" in response.data  # revenue
    assert b"Total" in response.data


def test_plans_list_shows_quantity_sold(client, login, plan_id):
    login()
    _record(client, plan_id, quantity_sold="120")
    response = client.get("/plans/")
    assert f'href="/sales/new?plan={plan_id}"'.encode() not in response.data
    assert re.search(rb">\s*120\s*</td>", response.data)


def test_one_sales_summary_per_plan(app, client, login, plan_id):
    login()
    _record(client, plan_id)
    for response in (client.get(f"/sales/new?plan={plan_id}"), _record(client, plan_id)):
        assert response.status_code == 302
    response = client.get("/sales/")
    assert b"are already recorded." in response.data
    with app.app_context():
        assert Sales.query.filter_by(plan_id=plan_id).count() == 1


@pytest.mark.parametrize("data, message", [
    ({"quantity_sold": ""}, b"Quantity sold is required."),
    ({"quantity_sold": "-1"}, b"Enter a whole number of cupcakes, 0 or more."),
    ({"quantity_sold": "12.5"}, b"Enter a whole number of cupcakes, 0 or more."),
    ({"quantity_sold": "136"}, b"Cannot be more than the 135 cupcakes baked for the plan."),
    ({"revenue": ""}, b"Revenue is required."),
    ({"revenue": "lots"}, b"Enter an amount."),
    ({"revenue": "-1"}, b"Revenue cannot be negative."),
    ({"revenue": "10.555"}, b"Use at most 2 decimal places."),
])
def test_record_sales_invalid(app, client, login, plan_id, data, message):
    login()
    response = client.post(f"/sales/new?plan={plan_id}", data={"quantity_sold": "120", "revenue": "1800"} | data)
    assert response.status_code == 400
    assert message in response.data
    with app.app_context():
        assert Sales.query.filter_by(plan_id=plan_id).count() == 0


def test_sold_out_and_free_cupcakes_are_valid(app, client, login, plan_id):
    # Selling every cupcake, with zero revenue (e.g. given away), is allowed
    login()
    assert _record(client, plan_id, quantity_sold="135", revenue="0").status_code == 302


@pytest.mark.parametrize("plan", ["", "not-a-uuid", str(uuid.uuid4())])
def test_unknown_plan(client, login, plan):
    login()
    assert client.get(f"/sales/new?plan={plan}").status_code == 404


def test_nav_shows_sales_link(client, login):
    login()
    assert b'href="/sales/"' in client.get("/profile/").data

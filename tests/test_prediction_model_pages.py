import uuid
from decimal import Decimal

import pytest

from app import db
from app.models import Cupcake, CupcakeType, PredictionModel, Store


@pytest.fixture
def ids(app):
    """A new cupcake and the seeded Riga Centre store."""
    with app.app_context():
        cupcake = Cupcake(name=f"Forecast Cupcake {uuid.uuid4().hex[:8]}",
                          cupcake_type=CupcakeType.query.filter_by(name="Classic").one())
        db.session.add(cupcake)
        db.session.commit()
        return {"cupcake": cupcake.id, "store": Store.query.filter_by(name="Riga Centre").one().id}


def _case_3(ids, **changes):
    """Form data for Case 3 from the lecture (d = 150, c = 10, p = 15, s = 2)."""
    return {
        "name": "Case 3",
        "cupcake": str(ids["cupcake"]),
        "store": str(ids["store"]),
        "average_demand": "150",
        "demand_std_dev": "30",
        "production_cost": "10",
        "selling_price": "15",
        "salvage_value": "2",
    } | changes


def test_list_requires_login(client):
    response = client.get("/prediction-models/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_new_forbidden_without_admin_role(client, login, ids):
    login(roles=["user"])
    assert client.get("/prediction-models/new").status_code == 403
    assert client.post("/prediction-models/new", data=_case_3(ids)).status_code == 403


def test_list_shows_add_link_only_to_admin(client, login):
    login(roles=["user"])
    assert b"Add prediction model" not in client.get("/prediction-models/").data
    login(roles=["admin"])
    assert b'href="/prediction-models/new"' in client.get("/prediction-models/").data


def test_new_form_lists_cupcakes_and_stores(client, login, ids):
    login(roles=["admin"])
    response = client.get("/prediction-models/new")
    assert response.status_code == 200
    assert str(ids["cupcake"]).encode() in response.data
    assert "Āgenskalns".encode() in response.data


def test_create_prediction_model(app, client, login, ids):
    login(roles=["admin"])
    # Decimal comma is accepted
    response = client.post("/prediction-models/new", data=_case_3(ids, selling_price="15,00"),
                           follow_redirects=True)

    assert response.status_code == 200
    assert b"Prediction model &#34;Case 3&#34; added." in response.data
    # Cu = 5, Co = 8, CR = 5 / 13
    assert b"5.00" in response.data
    assert b"8.00" in response.data
    assert b"0.38" in response.data
    with app.app_context():
        model = PredictionModel.query.filter_by(cupcake_id=ids["cupcake"]).one()
        assert model.store_id == ids["store"]
        assert model.average_demand == 150
        assert model.selling_price == Decimal("15.00")


def test_create_prediction_model_required_fields(client, login):
    login(roles=["admin"])
    response = client.post("/prediction-models/new", data={})
    assert response.status_code == 400
    assert b"Name is required." in response.data
    assert b"Choose a cupcake." in response.data
    assert b"Choose a store." in response.data
    assert response.data.count(b"This field is required.") == 5


@pytest.mark.parametrize("changes, message", [
    ({"average_demand": "many"}, b"Enter a number."),
    ({"demand_std_dev": "-1"}, b"The number cannot be negative."),
    ({"production_cost": "10.555"}, b"Use at most 2 decimal places."),
    ({"selling_price": "10"}, b"Selling price must be higher than production cost."),
    ({"salvage_value": "10"}, b"Salvage value must be lower than production cost."),
    ({"cupcake": str(uuid.uuid4())}, b"Choose a cupcake."),
])
def test_create_prediction_model_invalid(client, login, ids, changes, message):
    login(roles=["admin"])
    response = client.post("/prediction-models/new", data=_case_3(ids, **changes))
    assert response.status_code == 400
    assert message in response.data
    # The typed values stay in the form
    assert b'value="Case 3"' in response.data


def test_nav_shows_prediction_models_link(client, login):
    login()
    assert b'href="/prediction-models/"' in client.get("/profile/").data


# --- Delete (admin only)

def _add_model(app, ids, name="To delete"):
    with app.app_context():
        model = PredictionModel(name=name, cupcake_id=ids["cupcake"], store_id=ids["store"],
                                average_demand=150, demand_std_dev=30, production_cost=Decimal("10"),
                                selling_price=Decimal("15"), salvage_value=Decimal("2"))
        db.session.add(model)
        db.session.commit()
        return model.id


def test_delete_forbidden_without_admin_role(app, client, login, ids):
    model_id = _add_model(app, ids)
    login(roles=["user"])
    assert client.post(f"/prediction-models/{model_id}/delete").status_code == 403
    with app.app_context():
        assert db.session.get(PredictionModel, model_id) is not None


def test_list_shows_delete_buttons_and_dialog_only_to_admin(app, client, login, ids):
    model_id = _add_model(app, ids)
    login(roles=["user"])
    response = client.get("/prediction-models/")
    assert b"delete-dialog" not in response.data
    assert f"/prediction-models/{model_id}/delete".encode() not in response.data

    login(roles=["admin"])
    response = client.get("/prediction-models/")
    assert b'<dialog id="delete-dialog"' in response.data
    assert f'data-url="/prediction-models/{model_id}/delete"'.encode() in response.data


def test_delete_prediction_model(app, client, login, ids):
    model_id = _add_model(app, ids, name="Old model")
    login(roles=["admin"])
    response = client.post(f"/prediction-models/{model_id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Prediction model &#34;Old model&#34; deleted." in response.data
    with app.app_context():
        assert db.session.get(PredictionModel, model_id) is None
        # The cupcake and the store stay
        assert db.session.get(Cupcake, ids["cupcake"]) is not None
        assert db.session.get(Store, ids["store"]) is not None


def test_delete_unknown_prediction_model(client, login):
    login(roles=["admin"])
    assert client.post(f"/prediction-models/{uuid.uuid4()}/delete").status_code == 404


def test_delete_requires_post(app, client, login, ids):
    model_id = _add_model(app, ids)
    login(roles=["admin"])
    assert client.get(f"/prediction-models/{model_id}/delete").status_code == 405

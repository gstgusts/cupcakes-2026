import uuid
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Cupcake, CupcakeType, PredictionModel, Store

# Case 3 from the lecture: d = 150, c = 10, p = 15, s = 2
CASE_3 = {
    "average_demand": 150,
    "demand_std_dev": 30,
    "production_cost": Decimal("10.00"),
    "selling_price": Decimal("15.00"),
    "salvage_value": Decimal("2.00"),
}


@pytest.fixture
def cupcake_id(app):
    with app.app_context():
        cupcake = Cupcake(name=f"Model Cupcake {uuid.uuid4().hex[:8]}",
                          cupcake_type=CupcakeType.query.filter_by(name="Classic").one())
        db.session.add(cupcake)
        db.session.commit()
        return cupcake.id


def _store_id(name="Riga Centre"):
    return Store.query.filter_by(name=name).one().id


def test_stores_are_seeded(app):
    with app.app_context():
        stores = {store.name: store.address for store in Store.query.all()}
    assert set(stores) == {"Riga Centre", "Āgenskalns"}
    assert all(stores.values())


def test_save_prediction_model(app, cupcake_id):
    with app.app_context():
        model = PredictionModel(name="Case 3", cupcake_id=cupcake_id, store_id=_store_id(), **CASE_3)
        db.session.add(model)
        db.session.commit()

        model = db.session.get(PredictionModel, model.id)
        assert model.cupcake.id == cupcake_id
        assert model.store.name == "Riga Centre"
        assert model in model.store.prediction_models


def test_costs_and_critical_ratio():
    model = PredictionModel(**CASE_3)
    assert model.underage_cost == Decimal("5.00")
    assert model.overage_cost == Decimal("8.00")
    assert model.critical_ratio == pytest.approx(5 / 13)


@pytest.mark.parametrize("changes", [
    {"average_demand": -1},
    {"demand_std_dev": -1},
    {"salvage_value": Decimal("-1.00")},
    {"salvage_value": Decimal("10.00")},  # salvage value must be below cost
    {"selling_price": Decimal("10.00")},  # price must be above cost
])
def test_invalid_parameters_are_rejected_by_database(app, cupcake_id, changes):
    with app.app_context():
        store_id = _store_id()
        db.session.add(PredictionModel(name="Invalid", cupcake_id=cupcake_id, store_id=store_id,
                                       **(CASE_3 | changes)))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_cupcake_with_prediction_model_cannot_be_deleted(app, cupcake_id):
    with app.app_context():
        db.session.add(PredictionModel(name="Keeps cupcake", cupcake_id=cupcake_id, store_id=_store_id(), **CASE_3))
        db.session.commit()

        db.session.delete(db.session.get(Cupcake, cupcake_id))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

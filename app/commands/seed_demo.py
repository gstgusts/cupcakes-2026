"""Demo data for lectures: cupcakes, prediction models and predictions.

Run with: flask --app run seed-demo   (or seed-demo.ps1 / seed-demo.sh in Docker)
Running it again adds only what is missing, so it is safe to repeat.
"""
from datetime import date, timedelta
from decimal import Decimal

import click
from flask.cli import with_appcontext

from ..models import Cupcake, CupcakeType, Prediction, PredictionModel, Store
from ..models.base import db
from ..services.forecast import recommended_quantity

# (name, type, description); types and stores come from the seed migrations
CUPCAKES = [
    ("Vanilla Bean", "Classic", "Vanilla sponge with vanilla bean buttercream"),
    ("Double Chocolate", "Classic", "Chocolate sponge with chocolate ganache"),
    ("Blueberry Oat", "Vegan", "Blueberries, oat milk and a crumble top"),
    ("Almond Cloud", "Gluten-free", "Almond flour sponge with whipped cream"),
    ("Gingerbread", "Seasonal", "Ginger, cinnamon and cream cheese frosting"),
]

# (cupcake, store, model name, d, σ, c, p, s)
PREDICTION_MODELS = [
    ("Vanilla Bean", "Riga Centre", "Case 3", 150, 30, "10", "15", "2"),  # lecture example: bake 141
    ("Vanilla Bean", "Āgenskalns", "Weekday", 90, 20, "10", "15", "2"),
    ("Double Chocolate", "Riga Centre", "High margin", 120, 25, "10", "25", "2"),  # CR > 0.5: bake more
    ("Double Chocolate", "Āgenskalns", "Slide 9", 150, 30, "20", "30", "5"),  # lecture example: bake 142
    ("Blueberry Oat", "Āgenskalns", "Weekday", 60, 15, "12", "18", "3"),
    ("Almond Cloud", "Riga Centre", "Weekday", 40, 10, "14", "20", "4"),
    ("Gingerbread", "Riga Centre", "Christmas", 80, 35, "9", "16", "1"),
    ("Gingerbread", "Āgenskalns", "Christmas", 50, 20, "6", "16", "1"),  # CR > 0.5: bake more
]

# Predictions for today and the next days
PREDICTION_DAYS = 7


@click.command("seed-demo")
@with_appcontext
def seed_demo():
    """Adds demo cupcakes, prediction models and predictions (only the missing ones)."""
    types = {t.name: t for t in CupcakeType.query.all()}
    stores = {s.name: s for s in Store.query.all()}
    added = {"cupcakes": 0, "prediction models": 0, "predictions": 0}

    cupcakes = {}
    for name, type_name, description in CUPCAKES:
        cupcake = Cupcake.query.filter_by(name=name).first()
        if cupcake is None:
            cupcake = Cupcake(name=name, cupcake_type=types[type_name], description=description)
            db.session.add(cupcake)
            added["cupcakes"] += 1
        cupcakes[name] = cupcake
    db.session.flush()

    days = [date.today() + timedelta(days=i) for i in range(PREDICTION_DAYS)]
    for cupcake_name, store_name, model_name, d, sd, c, p, s in PREDICTION_MODELS:
        cupcake, store = cupcakes[cupcake_name], stores[store_name]
        model = PredictionModel.query.filter_by(cupcake_id=cupcake.id, store_id=store.id, name=model_name).first()
        if model is None:
            model = PredictionModel(name=model_name, cupcake=cupcake, store=store,
                                    average_demand=d, demand_std_dev=sd, production_cost=Decimal(c),
                                    selling_price=Decimal(p), salvage_value=Decimal(s))
            db.session.add(model)
            db.session.flush()
            added["prediction models"] += 1

        existing = {p.date for p in Prediction.query.filter_by(prediction_model_id=model.id)}
        quantity = recommended_quantity(model.average_demand, model.demand_std_dev, model.critical_ratio)
        for day in days:
            if day not in existing:
                db.session.add(Prediction(prediction_model=model, date=day, recommended_quantity=quantity))
                added["predictions"] += 1

    db.session.commit()
    click.echo("Added " + ", ".join(f"{count} {what}" for what, count in added.items()) + ".")

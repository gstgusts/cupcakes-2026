from flask import jsonify
from sqlalchemy.orm import joinedload

from ..models import Cupcake, PredictionModel, Store
from ..services.token_auth import api_login_required
from . import api_bp


@api_bp.get("/prediction-models")
@api_login_required
def prediction_models():
    models = (
        PredictionModel.query
        .options(joinedload(PredictionModel.cupcake), joinedload(PredictionModel.store))
        .join(PredictionModel.cupcake).join(PredictionModel.store)
        .order_by(Cupcake.name.asc(), Store.name.asc(), PredictionModel.name.asc())
        .all()
    )
    return jsonify([prediction_model_json(m) for m in models])


def prediction_model_json(model):
    # Money is stored as Decimal; JSON numbers are enough for showing it in the apps
    return {
        "id": str(model.id),
        "name": model.name,
        "cupcake": {"id": str(model.cupcake.id), "name": model.cupcake.name},
        "store": {"id": str(model.store.id), "name": model.store.name},
        "average_demand": model.average_demand,
        "demand_std_dev": model.demand_std_dev,
        "production_cost": float(model.production_cost),
        "selling_price": float(model.selling_price),
        "salvage_value": float(model.salvage_value),
        "critical_ratio": model.critical_ratio,
    }

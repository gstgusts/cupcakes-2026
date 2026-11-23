import uuid

from flask import jsonify, request, url_for
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from ..models import Prediction, PredictionModel
from ..models.base import db
from ..services.forecast import recommended_quantity
from ..services.token_auth import api_login_required
from ..validations.prediction import to_date, validate_prediction
from . import api_bp

DUPLICATE = "This model already has a prediction for this date."

# Loads the model, cupcake and store together with each prediction (one query instead of one per row)
WITH_MODEL = joinedload(Prediction.prediction_model).options(
    joinedload(PredictionModel.cupcake), joinedload(PredictionModel.store)
)


@api_bp.get("/predictions")
@api_login_required
def predictions():
    rows = (
        Prediction.query.options(WITH_MODEL)
        .order_by(Prediction.date.desc(), Prediction.created_at.desc())
        .all()
    )
    return jsonify([prediction_json(p) for p in rows])


@api_bp.post("/predictions")
@api_login_required
def create_prediction():
    # Only JSON bodies: a browser cannot send JSON to another site without CORS permission,
    # which also protects the session-cookie login against cross-site requests
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(errors={"request": "Send a JSON object with prediction_model_id and date."}), 400

    date_text = body.get("date")
    form = {
        "model": _parse_uuid(body.get("prediction_model_id")),
        "date": date_text.strip() if isinstance(date_text, str) else "",
    }
    model_ids = {row.id for row in db.session.query(PredictionModel.id)}
    errors = validate_prediction(form, model_ids)
    if errors:
        # The form uses the field name "model"; the API uses "prediction_model_id"
        if "model" in errors:
            errors["prediction_model_id"] = errors.pop("model")
        return jsonify(errors=errors), 400

    model = db.session.get(PredictionModel, form["model"])
    prediction_date = to_date(form["date"])
    if Prediction.query.filter_by(prediction_model_id=model.id, date=prediction_date).first():
        return jsonify(errors={"date": DUPLICATE}), 409

    prediction = Prediction(
        prediction_model=model,
        date=prediction_date,
        recommended_quantity=recommended_quantity(model.average_demand, model.demand_std_dev, model.critical_ratio),
    )
    db.session.add(prediction)
    try:
        db.session.commit()
    except IntegrityError:
        # Another request saved the same model and date after our check
        db.session.rollback()
        return jsonify(errors={"date": DUPLICATE}), 409

    response = jsonify(prediction_json(prediction))
    response.status_code = 201
    # The Flask page of the new prediction
    response.headers["Location"] = url_for("predictions.show", prediction_id=prediction.id)
    return response


def prediction_json(prediction):
    model = prediction.prediction_model
    return {
        "id": str(prediction.id),
        "date": prediction.date.isoformat(),
        "recommended_quantity": prediction.recommended_quantity,
        "prediction_model": {"id": str(model.id), "name": model.name},
        "cupcake": {"id": str(model.cupcake.id), "name": model.cupcake.name},
        "store": {"id": str(model.store.id), "name": model.store.name},
        "created_at": prediction.created_at.isoformat(),
    }


def _parse_uuid(value):
    """UUID from the JSON body, or None if it is missing or invalid."""
    try:
        return uuid.UUID(value) if isinstance(value, str) and value else None
    except ValueError:
        return None

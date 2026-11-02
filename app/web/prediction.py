import uuid
from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload

from ..models import Cupcake, Plan, Prediction, PredictionModel, Store
from ..models.base import db
from ..services.auth import login_required
from ..services.forecast import recommended_quantity, z_score
from ..validations.prediction import to_date, validate_prediction

predictions_bp = Blueprint("predictions", __name__, url_prefix="/predictions")

# Loads the model, cupcake and store together with each prediction (one query instead of one per row)
WITH_MODEL = joinedload(Prediction.prediction_model).options(
    joinedload(PredictionModel.cupcake), joinedload(PredictionModel.store)
)


@predictions_bp.get("/")
@login_required
def index():
    predictions = (
        Prediction.query.options(WITH_MODEL)
        .order_by(Prediction.date.desc(), Prediction.created_at.desc())
        .all()
    )
    return render_template("predictions/index.html", predictions=predictions)


@predictions_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    models = (
        PredictionModel.query
        .options(joinedload(PredictionModel.cupcake), joinedload(PredictionModel.store))
        .join(PredictionModel.cupcake).join(PredictionModel.store)
        .order_by(Cupcake.name.asc(), Store.name.asc(), PredictionModel.name.asc())
        .all()
    )

    def show_form(form, errors=None, status=200, existing=None, error=None):
        return render_template("predictions/new.html", form=form, errors=errors or {}, models=models,
                               existing=existing, error=error), status

    if request.method == "GET":
        # Cupcakes are baked the day before, so the default is tomorrow
        return show_form({"model": _parse_uuid(request.args.get("model")),
                          "date": (date.today() + timedelta(days=1)).isoformat()})

    form = {"model": _parse_uuid(request.form.get("model")), "date": (request.form.get("date") or "").strip()}
    errors = validate_prediction(form, {m.id for m in models})
    if errors:
        return show_form(form, errors, 400)

    model = db.session.get(PredictionModel, form["model"])
    prediction_date = to_date(form["date"])
    existing = Prediction.query.filter_by(prediction_model_id=model.id, date=prediction_date).first()
    if existing:
        return show_form(form, {"date": "This model already has a prediction for this date."}, 400, existing)

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
        return show_form(form, {"date": "This model already has a prediction for this date."}, 400)
    except SQLAlchemyError:
        db.session.rollback()
        return show_form(form, status=500, error="Saving the prediction failed. Please try again.")

    flash("Prediction created.")
    return redirect(url_for("predictions.show", prediction_id=prediction.id))


@predictions_bp.get("/<uuid:prediction_id>")
@login_required
def show(prediction_id):
    prediction = db.get_or_404(Prediction, prediction_id, options=[WITH_MODEL])
    return show_page(prediction)


def show_page(prediction, status=200, **context):
    """Result page of a prediction. The plan pages use it to show confirmation errors."""
    model = prediction.prediction_model
    ratio = model.critical_ratio
    # The calculation steps, shown with the model's parameters
    z = z_score(ratio)
    steps = {
        "ratio": ratio,
        "z": z,
        "exact_quantity": model.average_demand + z * model.demand_std_dev,
    }
    # The plan for this cupcake, store and date, if one is confirmed (possibly from another model's prediction)
    plan = Plan.query.filter_by(cupcake_id=model.cupcake_id, store_id=model.store_id, date=prediction.date).first()
    context.setdefault("plan_form", {"quantity": str(prediction.recommended_quantity)})
    return render_template("predictions/show.html", prediction=prediction, model=model, steps=steps,
                           plan=plan, plan_errors=context.pop("plan_errors", {}), **context), status


def _parse_uuid(value):
    """UUID from the form or query string, or None if it is missing or invalid."""
    try:
        return uuid.UUID(value) if value else None
    except ValueError:
        return None

import uuid

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from ..auth import login_required, role_required
from ..models import Cupcake, PredictionModel, Store
from ..models.base import db
from ..validations.prediction_model import to_decimal, validate_prediction_model

prediction_models_bp = Blueprint("prediction_models", __name__, url_prefix="/prediction-models")

NUMBER_FIELDS = ("average_demand", "demand_std_dev", "production_cost", "selling_price", "salvage_value")


@prediction_models_bp.get("/")
@login_required
def index():
    # Loads the cupcake and store together with each model (one query instead of one per row)
    models = (
        PredictionModel.query
        .options(joinedload(PredictionModel.cupcake), joinedload(PredictionModel.store))
        .join(PredictionModel.cupcake).join(PredictionModel.store)
        .order_by(Cupcake.name.asc(), Store.name.asc(), PredictionModel.name.asc())
        .all()
    )
    return render_template("prediction_models/index.html", models=models)


@prediction_models_bp.route("/new", methods=["GET", "POST"])
@role_required("admin")
def new():
    cupcakes = Cupcake.query.order_by(Cupcake.name.asc()).all()
    stores = Store.query.order_by(Store.name.asc()).all()

    def show_form(form, errors=None, status=200, error=None):
        return render_template("prediction_models/new.html", form=form, errors=errors or {}, error=error,
                               cupcakes=cupcakes, stores=stores), status

    if request.method == "GET":
        return show_form({})

    form = {field: (request.form.get(field) or "").strip() for field in ("name",) + NUMBER_FIELDS}
    form["cupcake"] = _parse_uuid(request.form.get("cupcake"))
    form["store"] = _parse_uuid(request.form.get("store"))

    errors = validate_prediction_model(form, {c.id for c in cupcakes}, {s.id for s in stores})
    if errors:
        return show_form(form, errors, 400)

    model = PredictionModel(
        name=form["name"],
        cupcake_id=form["cupcake"],
        store_id=form["store"],
        **{field: to_decimal(form[field]) for field in NUMBER_FIELDS},
    )
    db.session.add(model)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return show_form(form, status=500, error="Saving the prediction model failed. Please try again.")

    flash(f'Prediction model "{model.name}" added.')
    return redirect(url_for("prediction_models.index"))


@prediction_models_bp.post("/<uuid:model_id>/delete")
@role_required("admin")
def delete(model_id):
    # The list asks for confirmation in a dialog before it posts here
    model = db.get_or_404(PredictionModel, model_id)
    db.session.delete(model)
    db.session.commit()
    flash(f'Prediction model "{model.name}" deleted.')
    return redirect(url_for("prediction_models.index"))


def _parse_uuid(value):
    """UUID from the form, or None if it is missing or invalid."""
    try:
        return uuid.UUID(value) if value else None
    except ValueError:
        return None

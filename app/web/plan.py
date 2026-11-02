import uuid

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload

from ..models import Plan, Prediction, User
from ..models.base import db
from ..services.auth import current_user, login_required
from ..validations.plan import validate_plan
from .prediction import WITH_MODEL, show_page

plans_bp = Blueprint("plans", __name__, url_prefix="/plans")

PLAN_EXISTS = "A plan for this cupcake, store and date is already confirmed."


@plans_bp.get("/")
@login_required
def index():
    plans = (
        Plan.query
        .options(joinedload(Plan.cupcake), joinedload(Plan.store),
                 joinedload(Plan.prediction), joinedload(Plan.confirmed_by), joinedload(Plan.sales))
        .order_by(Plan.date.desc(), Plan.confirmed_at.desc())
        .all()
    )
    return render_template("plans/index.html", plans=plans)


@plans_bp.post("/new")
@login_required
def new():
    """Confirms a plan from a prediction (the form is on the prediction page)."""
    prediction_id = _parse_uuid(request.form.get("prediction"))
    if prediction_id is None:
        abort(404)
    prediction = db.get_or_404(Prediction, prediction_id, options=[WITH_MODEL])
    model = prediction.prediction_model
    form = {"quantity": (request.form.get("quantity") or "").strip()}

    def show_errors(errors, status=400, error=None):
        return show_page(prediction, status, plan_form=form, plan_errors=errors, error=error)

    # The plan records who confirmed it, so the logged-in user needs a profile
    user = User.find_by_email(current_user()["email"])
    if user is None:
        return show_errors({}, 403, "Create your profile before confirming plans.")

    errors = validate_plan(form)
    if errors:
        return show_errors(errors)

    plan = Plan(
        date=prediction.date,
        cupcake_id=model.cupcake_id,
        store_id=model.store_id,
        prediction=prediction,
        quantity_confirmed=int(form["quantity"]),
        confirmed_by=user,
    )
    db.session.add(plan)
    try:
        db.session.commit()
    except IntegrityError:
        # A plan for this cupcake, store and date exists (the page did not show it, or it was saved meanwhile)
        db.session.rollback()
        return show_errors({}, 409, PLAN_EXISTS)
    except SQLAlchemyError:
        db.session.rollback()
        return show_errors({}, 500, "Saving the plan failed. Please try again.")

    flash(f"Plan confirmed: bake {plan.quantity_confirmed} cupcakes.")
    return redirect(url_for("plans.index"))


def _parse_uuid(value):
    """UUID from the form, or None if it is missing or invalid."""
    try:
        return uuid.UUID(value) if value else None
    except ValueError:
        return None

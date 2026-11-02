import uuid

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload

from ..models import Plan, Prediction, Sales
from ..models.base import db
from ..services.auth import login_required
from ..validations.prediction_model import to_decimal
from ..validations.sales import validate_sales

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")

# Loads the plan with its cupcake, store and prediction model (one query instead of one per row)
WITH_PLAN = joinedload(Sales.plan).options(
    joinedload(Plan.cupcake),
    joinedload(Plan.store),
    joinedload(Plan.prediction).joinedload(Prediction.prediction_model),
)


@sales_bp.get("/")
@login_required
def index():
    sales = Sales.query.options(WITH_PLAN).order_by(Sales.date.desc(), Sales.recorded_at.desc()).all()
    totals = {
        "baked": sum(s.plan.quantity_confirmed for s in sales),
        "sold": sum(s.quantity_sold for s in sales),
        "revenue": sum((s.revenue for s in sales), start=0),
    }
    return render_template("sales/index.html", sales=sales, totals=totals)


@sales_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Records the sales summary of a plan (?plan=<id>, linked from the plans list)."""
    plan_id = _parse_uuid(request.values.get("plan"))
    if plan_id is None:
        abort(404)
    plan = db.get_or_404(Plan, plan_id, options=[
        joinedload(Plan.cupcake), joinedload(Plan.store),
        joinedload(Plan.prediction).joinedload(Prediction.prediction_model),
    ])
    if plan.sales:
        flash(f"Sales for {plan.cupcake.name} at {plan.store.name} on {plan.date} are already recorded.", "error")
        return redirect(url_for("sales.index"))

    def show_form(form, errors=None, status=200, error=None):
        return render_template("sales/new.html", plan=plan, form=form, errors=errors or {}, error=error), status

    if request.method == "GET":
        return show_form({})

    form = {field: (request.form.get(field) or "").strip() for field in ("quantity_sold", "revenue")}
    errors = validate_sales(form, plan.quantity_confirmed)
    if errors:
        return show_form(form, errors, 400)

    sales = Sales(plan=plan, date=plan.date, quantity_sold=int(form["quantity_sold"]),
                  revenue=to_decimal(form["revenue"]))
    db.session.add(sales)
    try:
        db.session.commit()
    except IntegrityError:
        # Another request recorded this plan's sales after our check
        db.session.rollback()
        return show_form(form, status=409, error="Sales for this plan are already recorded.")
    except SQLAlchemyError:
        db.session.rollback()
        return show_form(form, status=500, error="Saving the sales failed. Please try again.")

    flash(f"Sales recorded: {sales.quantity_sold} cupcakes sold.")
    return redirect(url_for("sales.index"))


def _parse_uuid(value):
    """UUID from the query string or form, or None if it is missing or invalid."""
    try:
        return uuid.UUID(value) if value else None
    except ValueError:
        return None

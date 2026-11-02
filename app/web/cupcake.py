import uuid

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload

from ..auth import login_required, role_required
from ..models import Cupcake, CupcakeType
from ..models.base import db
from ..validations.cupcake import validate_cupcake

cupcakes_bp = Blueprint("cupcakes", __name__, url_prefix="/cupcakes")


@cupcakes_bp.get("/")
@login_required
def index():
    q = (request.args.get("q") or "").strip()
    type_id = _parse_uuid(request.args.get("type"))

    # Loads the type together with each cupcake (one query instead of one per row)
    query = Cupcake.query.options(joinedload(Cupcake.cupcake_type))
    if q:
        like = f"%{q}%"
        query = query.filter(Cupcake.name.ilike(like) | Cupcake.description.ilike(like))
    if type_id:
        query = query.filter(Cupcake.cupcake_type_id == type_id)
    cupcakes = query.order_by(Cupcake.name.asc()).all()

    types = _types()
    return render_template("cupcakes/index.html", cupcakes=cupcakes, types=types, q=q, type_id=type_id)


@cupcakes_bp.route("/new", methods=["GET", "POST"])
@role_required("admin")
def new():
    if request.method == "GET":
        return render_template("cupcakes/form.html", cupcake=None, form={}, errors={}, types=_types())
    return _save(Cupcake())


@cupcakes_bp.route("/<uuid:cupcake_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit(cupcake_id):
    cupcake = db.get_or_404(Cupcake, cupcake_id)
    if request.method == "GET":
        form = {"name": cupcake.name, "type": cupcake.cupcake_type_id, "description": cupcake.description or ""}
        return render_template("cupcakes/form.html", cupcake=cupcake, form=form, errors={}, types=_types())
    return _save(cupcake)


def _save(cupcake):
    """Validates the posted form and saves a new (cupcake.id is None) or existing cupcake."""
    is_new = cupcake.id is None
    types = _types()
    form = {
        "name": (request.form.get("name") or "").strip(),
        "type": _parse_uuid(request.form.get("type")),
        "description": (request.form.get("description") or "").strip(),
    }

    def show_form(status, errors=None, error=None):
        return render_template("cupcakes/form.html", cupcake=None if is_new else cupcake, form=form,
                               errors=errors or {}, error=error, types=types), status

    errors = validate_cupcake(form, {t.id for t in types})
    if not errors and _name_taken(form["name"], cupcake.id):
        errors["name"] = "A cupcake with this name already exists."
    if errors:
        return show_form(400, errors)

    cupcake.name = form["name"]
    cupcake.cupcake_type_id = form["type"]
    cupcake.description = form["description"] or None
    if is_new:
        db.session.add(cupcake)
    try:
        db.session.commit()
    except IntegrityError:
        # Another request saved the same name after our check
        db.session.rollback()
        return show_form(400, {"name": "A cupcake with this name already exists."})
    except SQLAlchemyError:
        db.session.rollback()
        return show_form(500, error="Saving the cupcake failed. Please try again.")

    flash(f'Cupcake "{cupcake.name}" added.' if is_new else f'Cupcake "{cupcake.name}" saved.')
    return redirect(url_for("cupcakes.index"))


def _name_taken(name, exclude_id):
    """True if another cupcake already has this name (case-insensitive)."""
    query = db.session.query(Cupcake.id).filter(func.lower(Cupcake.name) == name.lower())
    if exclude_id:
        query = query.filter(Cupcake.id != exclude_id)
    return query.first() is not None


def _types():
    return CupcakeType.query.order_by(CupcakeType.name.asc()).all()


def _parse_uuid(value):
    """UUID from the query string, or None if it is missing or invalid."""
    try:
        return uuid.UUID(value) if value else None
    except ValueError:
        return None

import uuid

from flask import Blueprint, render_template, request
from sqlalchemy.orm import joinedload

from ..auth import login_required
from ..models import Cupcake, CupcakeType

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

    types = CupcakeType.query.order_by(CupcakeType.name.asc()).all()
    return render_template("cupcakes/index.html", cupcakes=cupcakes, types=types, q=q, type_id=type_id)


def _parse_uuid(value):
    """UUID from the query string, or None if it is missing or invalid."""
    try:
        return uuid.UUID(value) if value else None
    except ValueError:
        return None

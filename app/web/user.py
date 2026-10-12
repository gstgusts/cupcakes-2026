from flask import Blueprint, render_template, request

from ..auth import role_required
from ..models import User

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.get("/")
@role_required("admin")
def index():
    q = (request.args.get("q") or "").strip()
    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            User.name.ilike(like) | User.surname.ilike(like) | User.email.ilike(like)
        )
    users = query.order_by(User.surname.asc(), User.name.asc()).all()
    return render_template("users/index.html", users=users, q=q)

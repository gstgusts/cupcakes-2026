from flask import Blueprint, render_template
from sqlalchemy import func

from ..auth import current_user, login_required
from ..models import User

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.get("/")
@login_required
def details():
    email = current_user()["email"]
    # Keycloak user is linked to the stored user by email (case-insensitive)
    profile = User.query.filter(func.lower(User.email) == email.lower()).first()
    if profile is None:
        return render_template("profile/details.html", profile=None, email=email), 404
    return render_template("profile/details.html", profile=profile, email=email)

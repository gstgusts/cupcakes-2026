from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

from ..models import User
from ..models.base import db
from ..services.auth import current_user, login_required
from ..validations.profile import validate_person

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.get("/")
@login_required
def details():
    email = current_user()["email"]
    profile = User.find_by_email(email)
    if profile is None:
        return render_template("profile/details.html", profile=None, email=email), 404
    return render_template("profile/details.html", profile=profile, email=email)


@profile_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """Creates the profile of the logged-in user if it is missing, otherwise updates it."""
    identity = current_user()
    email = identity["email"]
    profile = User.find_by_email(email)
    is_new = profile is None

    if request.method == "GET":
        if profile:
            form = {"name": profile.name, "surname": profile.surname}
        else:
            # Suggest the names from the Keycloak account
            form = {"name": identity.get("first_name", ""), "surname": identity.get("last_name", "")}
        return render_template("profile/edit.html", form=form, errors={}, email=email, is_new=is_new)

    form = {field: (request.form.get(field) or "").strip() for field in ("name", "surname")}
    errors = validate_person(form)
    if errors:
        return render_template("profile/edit.html", form=form, errors=errors, email=email, is_new=is_new), 400

    if is_new:
        # The email comes from the Keycloak login, which links the new profile to this account
        profile = User(email=email.lower())
        db.session.add(profile)
    profile.name = form["name"]
    profile.surname = form["surname"]
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return render_template("profile/edit.html", form=form, errors={}, email=email, is_new=is_new,
                               error="Saving the profile failed. Please try again."), 500

    flash("Profile created." if is_new else "Profile saved.")
    return redirect(url_for("profile.details"))

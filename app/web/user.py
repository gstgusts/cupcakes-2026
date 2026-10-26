import secrets
import string

from flask import Blueprint, render_template, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from .. import keycloak_admin
from ..auth import role_required
from ..keycloak_admin import KeycloakConflict, KeycloakError
from ..models import User
from ..models.base import db
from ..validation import validate_email, validate_person

users_bp = Blueprint("users", __name__, url_prefix="/users")

PASSWORD_SPECIALS = "!#$%&*+-=?@^_"


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


@users_bp.route("/new", methods=["GET", "POST"])
@role_required("admin")
def new():
    if request.method == "GET":
        return render_template("users/new.html", form={}, errors={})

    form = {field: (request.form.get(field) or "").strip() for field in ("name", "surname", "email")}
    form["email"] = form["email"].lower()

    errors = validate_person(form) | validate_email(form)
    if not errors:
        # The email links our profile to the Keycloak account, so it must be free in both places
        try:
            if _profile_exists(form["email"]):
                errors["email"] = "A user profile with this email already exists."
            elif keycloak_admin.email_exists(form["email"]):
                errors["email"] = "A Keycloak account with this email already exists."
        except KeycloakError as e:
            return render_template("users/new.html", form=form, errors={}, error=str(e)), 502
    if errors:
        return render_template("users/new.html", form=form, errors=errors), 400

    password = _temporary_password()
    try:
        keycloak_id = keycloak_admin.create_user(form["email"], form["name"], form["surname"], password)
    except KeycloakConflict as e:
        return render_template("users/new.html", form=form, errors={"email": str(e)}), 400
    except KeycloakError as e:
        return render_template("users/new.html", form=form, errors={}, error=str(e)), 502

    user = User(name=form["name"], surname=form["surname"], email=form["email"])
    db.session.add(user)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        # Keycloak and our database share no transaction: undo the Keycloak account by hand
        try:
            keycloak_admin.delete_user(keycloak_id)
        except KeycloakError:
            pass
        error = "Saving the user profile failed, so the Keycloak account was removed again."
        return render_template("users/new.html", form=form, errors={}, error=error), 500

    # The temporary password is shown only once, on this page
    return render_template("users/created.html", user=user, password=password)

# Test if a profile with the given email already exists in our database. Keycloak is checked separately.
def _profile_exists(email):
    return db.session.query(User.id).filter(func.lower(User.email) == email.lower()).first() is not None


def _temporary_password(length=12):
    """Random password with upper and lower case letters, digits and a special character."""
    alphabet = string.ascii_letters + string.digits + PASSWORD_SPECIALS
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password) and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password) and any(c in PASSWORD_SPECIALS for c in password)):
            return password

"""Form validation shared by the profile and user pages. Each function returns {field: message}."""
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_person(form):
    """Checks the name and surname fields."""
    errors = {}
    if not form["name"]:
        errors["name"] = "First name is required."
    elif len(form["name"]) > 100:
        errors["name"] = "First name can be at most 100 characters."
    if not form["surname"]:
        errors["surname"] = "Last name is required."
    elif len(form["surname"]) > 100:
        errors["surname"] = "Last name can be at most 100 characters."
    return errors


def validate_email(form):
    """Checks the email field."""
    if not form["email"]:
        return {"email": "Email address is required."}
    if len(form["email"]) > 255 or not EMAIL_RE.match(form["email"]):
        return {"email": "Enter a valid email address."}
    return {}

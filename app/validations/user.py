"""Validation of the fields an admin enters when adding a user."""
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(form):
    """Checks the email field."""
    if not form["email"]:
        return {"email": "Email address is required."}
    if len(form["email"]) > 255 or not EMAIL_RE.match(form["email"]):
        return {"email": "Enter a valid email address."}
    return {}

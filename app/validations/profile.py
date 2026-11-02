"""Validation of the profile fields (also used when an admin adds a user)."""


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

"""Validation of the cupcake add and edit form."""


def validate_cupcake(form, type_ids):
    """Checks the cupcake fields. type_ids are the ids of the existing cupcake types."""
    errors = {}
    if not form["name"]:
        errors["name"] = "Name is required."
    elif len(form["name"]) > 100:
        errors["name"] = "Name can be at most 100 characters."
    if form["type"] is None:
        errors["type"] = "Choose a cupcake type."
    elif form["type"] not in type_ids:
        errors["type"] = "Choose a valid cupcake type."
    if len(form["description"]) > 1000:
        errors["description"] = "Description can be at most 1000 characters."
    return errors

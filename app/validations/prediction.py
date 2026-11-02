"""Validation of the new prediction form."""
from datetime import date


def to_date(text):
    """Date from the form (YYYY-MM-DD, as sent by <input type="date">), or None if it is not valid."""
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def validate_prediction(form, model_ids):
    """Checks the prediction fields. model_ids are the ids of the existing prediction models."""
    errors = {}
    if form["model"] not in model_ids:
        errors["model"] = "Choose a prediction model."
    if not form["date"]:
        errors["date"] = "Date is required."
    elif to_date(form["date"]) is None:
        errors["date"] = "Enter a valid date."
    return errors

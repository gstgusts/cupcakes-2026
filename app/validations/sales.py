"""Validation of the daily sales summary form."""
from .prediction_model import MAX_MONEY, to_decimal


def validate_sales(form, quantity_confirmed):
    """Checks quantity sold and revenue. quantity_confirmed is the plan's number of baked cupcakes."""
    errors = {}

    text = form["quantity_sold"]
    if not text:
        errors["quantity_sold"] = "Quantity sold is required."
    # isascii(): isdigit() alone also accepts characters like "²" that int() cannot read
    elif not (text.isascii() and text.isdigit()):
        errors["quantity_sold"] = "Enter a whole number of cupcakes, 0 or more."
    elif int(text) > quantity_confirmed:
        errors["quantity_sold"] = f"Cannot be more than the {quantity_confirmed} cupcakes baked for the plan."

    revenue = to_decimal(form["revenue"]) if form["revenue"] else None
    if not form["revenue"]:
        errors["revenue"] = "Revenue is required."
    elif revenue is None:
        errors["revenue"] = "Enter an amount."
    elif revenue < 0:
        errors["revenue"] = "Revenue cannot be negative."
    elif revenue > MAX_MONEY:
        errors["revenue"] = f"Revenue can be at most {MAX_MONEY}."
    elif revenue != round(revenue, 2):
        errors["revenue"] = "Use at most 2 decimal places."
    return errors

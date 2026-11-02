"""Validation of the prediction model form."""
from decimal import Decimal, InvalidOperation

MAX_DEMAND = Decimal("1000000")
# Numeric(10, 2): at most 8 digits before the decimal point
MAX_MONEY = Decimal("99999999.99")


def to_decimal(text):
    """Number typed in the form ("12.5" or "12,5"), or None if it is not a number."""
    try:
        value = Decimal(text.replace(",", ".").replace(" ", ""))
    except InvalidOperation:
        return None
    return value if value.is_finite() else None


def validate_prediction_model(form, cupcake_ids, store_ids):
    """Checks the prediction model fields. cupcake_ids and store_ids are the ids that exist."""
    errors = {}
    if not form["name"]:
        errors["name"] = "Name is required."
    elif len(form["name"]) > 100:
        errors["name"] = "Name can be at most 100 characters."
    if form["cupcake"] not in cupcake_ids:
        errors["cupcake"] = "Choose a cupcake."
    if form["store"] not in store_ids:
        errors["store"] = "Choose a store."

    for field in ("average_demand", "demand_std_dev"):
        error = _number_error(form[field], MAX_DEMAND, decimals=None)
        if error:
            errors[field] = error
    for field in ("production_cost", "selling_price", "salvage_value"):
        error = _number_error(form[field], MAX_MONEY, decimals=2)
        if error:
            errors[field] = error

    # Both costs must be positive, otherwise the critical ratio is not defined
    cost, price, salvage = (to_decimal(form[f]) for f in ("production_cost", "selling_price", "salvage_value"))
    if "production_cost" not in errors and "selling_price" not in errors and price <= cost:
        errors["selling_price"] = "Selling price must be higher than production cost."
    if "production_cost" not in errors and "salvage_value" not in errors and salvage >= cost:
        errors["salvage_value"] = "Salvage value must be lower than production cost."
    return errors


def _number_error(text, maximum, decimals):
    """Error message for one number field, or None if the number is valid."""
    if not text:
        return "This field is required."
    value = to_decimal(text)
    if value is None:
        return "Enter a number."
    if value < 0:
        return "The number cannot be negative."
    if value > maximum:
        return f"The number can be at most {maximum}."
    if decimals is not None and value != round(value, decimals):
        return f"Use at most {decimals} decimal places."
    return None

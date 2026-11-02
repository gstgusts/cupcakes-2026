"""Validation of the plan confirmation form."""

MAX_QUANTITY = 100000


def validate_plan(form):
    """Checks the confirmed quantity (a whole number of cupcakes)."""
    text = form["quantity"]
    if not text:
        return {"quantity": "Quantity is required."}
    # isascii(): isdigit() alone also accepts characters like "²" that int() cannot read
    if not (text.isascii() and text.isdigit()):
        return {"quantity": "Enter a whole number of cupcakes, 0 or more."}
    if int(text) > MAX_QUANTITY:
        return {"quantity": f"Quantity can be at most {MAX_QUANTITY}."}
    return {}

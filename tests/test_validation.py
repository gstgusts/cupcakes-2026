import uuid
from decimal import Decimal

import pytest

from app.validations.cupcake import validate_cupcake
from app.validations.cupcake_image import detect_image_type, validate_cupcake_image
from app.validations.plan import validate_plan
from app.validations.prediction_model import to_decimal, validate_prediction_model
from app.validations.profile import validate_person
from app.validations.sales import validate_sales
from app.validations.user import validate_email
from app.web.user import PASSWORD_SPECIALS, _temporary_password


def test_valid_person_has_no_errors():
    assert validate_person({"name": "Anna", "surname": "Berzina"}) == {}


def test_person_name_and_surname_are_required():
    errors = validate_person({"name": "", "surname": ""})
    assert set(errors) == {"name", "surname"}


def test_person_name_too_long():
    errors = validate_person({"name": "a" * 101, "surname": "Berzina"})
    assert set(errors) == {"name"}


@pytest.mark.parametrize("email", ["anna@example.com", "a.b+c@sub.example.lv"])
def test_valid_email(email):
    assert validate_email({"email": email}) == {}


@pytest.mark.parametrize("email", ["", "anna", "anna@example", "an na@example.com", "a@b.c" + "x" * 255])
def test_invalid_email(email):
    assert "email" in validate_email({"email": email})


def test_temporary_password_meets_keycloak_rules():
    for _ in range(50):
        password = _temporary_password()
        assert len(password) == 12
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in PASSWORD_SPECIALS for c in password)


def test_valid_cupcake_has_no_errors():
    type_id = uuid.uuid4()
    form = {"name": "Vanilla Dream", "type": type_id, "description": ""}
    assert validate_cupcake(form, {type_id}) == {}


def test_cupcake_name_and_type_are_required():
    errors = validate_cupcake({"name": "", "type": None, "description": ""}, set())
    assert set(errors) == {"name", "type"}


def test_cupcake_type_must_exist():
    errors = validate_cupcake({"name": "Vanilla Dream", "type": uuid.uuid4(), "description": ""}, {uuid.uuid4()})
    assert set(errors) == {"type"}


def test_cupcake_name_and_description_too_long():
    type_id = uuid.uuid4()
    errors = validate_cupcake({"name": "a" * 101, "type": type_id, "description": "a" * 1001}, {type_id})
    assert set(errors) == {"name", "description"}


@pytest.mark.parametrize("data, content_type", [
    (b"\x89PNG\r\n\x1a\n...", "image/png"),
    (b"\xff\xd8\xff\xe0...", "image/jpeg"),
    (b"GIF89a...", "image/gif"),
    (b"RIFF\x00\x00\x00\x00WEBPVP8 ", "image/webp"),
    (b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", None),
    (b"%PDF-1.7", None),
])
def test_detect_image_type(data, content_type):
    assert detect_image_type(data) == content_type


def test_cupcake_image_file_is_required():
    assert set(validate_cupcake_image(b"", "")) == {"image"}


def test_cupcake_image_description_too_long():
    assert set(validate_cupcake_image(b"GIF89a...", "a" * 251)) == {"description"}


@pytest.mark.parametrize("text, value", [
    ("12", Decimal("12")),
    ("12.5", Decimal("12.5")),
    ("12,5", Decimal("12.5")),
    ("1 000", Decimal("1000")),
    ("abc", None),
    ("", None),
    ("NaN", None),
    ("Infinity", None),
])
def test_to_decimal(text, value):
    assert to_decimal(text) == value


CUPCAKE_ID, STORE_ID = uuid.uuid4(), uuid.uuid4()


def _prediction_model_form(**changes):
    return {
        "name": "Case 3", "cupcake": CUPCAKE_ID, "store": STORE_ID,
        "average_demand": "150", "demand_std_dev": "30",
        "production_cost": "10", "selling_price": "15", "salvage_value": "2",
    } | changes



def test_valid_prediction_model_has_no_errors():
    assert validate_prediction_model(_prediction_model_form(), {CUPCAKE_ID}, {STORE_ID}) == {}


def test_prediction_model_salvage_value_can_be_zero():
    form = _prediction_model_form(salvage_value="0")
    assert validate_prediction_model(form, {CUPCAKE_ID}, {STORE_ID}) == {}


def test_prediction_model_money_too_large():
    form = _prediction_model_form(selling_price="100000000")
    assert set(validate_prediction_model(form, {CUPCAKE_ID}, {STORE_ID})) == {"selling_price"}


def test_prediction_model_cost_comparison_skipped_when_cost_invalid():
    # Only the invalid field is reported, not "price must be higher than cost" as well
    form = _prediction_model_form(production_cost="abc")
    assert set(validate_prediction_model(form, {CUPCAKE_ID}, {STORE_ID})) == {"production_cost"}


@pytest.mark.parametrize("quantity", ["0", "141", "100000"])
def test_valid_plan_quantity(quantity):
    assert validate_plan({"quantity": quantity}) == {}


@pytest.mark.parametrize("quantity", ["", "abc", "-1", "1.5", "1e3", "²", "100001"])
def test_invalid_plan_quantity(quantity):
    assert set(validate_plan({"quantity": quantity})) == {"quantity"}


def test_valid_sales_has_no_errors():
    assert validate_sales({"quantity_sold": "120", "revenue": "1800,50"}, 135) == {}


def test_sales_fields_are_required():
    assert set(validate_sales({"quantity_sold": "", "revenue": ""}, 135)) == {"quantity_sold", "revenue"}


def test_sales_cannot_exceed_baked_quantity():
    assert set(validate_sales({"quantity_sold": "136", "revenue": "0"}, 135)) == {"quantity_sold"}

import uuid

import pytest

from app.validations.cupcake import validate_cupcake
from app.validations.profile import validate_person
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

import uuid

import pytest

from app import db
from app.models import Cupcake, CupcakeType


@pytest.fixture(scope="module")
def cupcakes(app):
    """One cupcake each for two of the seeded types (migration 0004); returns the type ids."""
    with app.app_context():
        classic = CupcakeType.query.filter_by(name="Classic").one()
        vegan = CupcakeType.query.filter_by(name="Vegan").one()
        db.session.add_all([
            Cupcake(name="Vanilla Dream", description="Vanilla sponge with buttercream", cupcake_type=classic),
            Cupcake(name="Berry Bliss", description="Raspberry and oat milk", cupcake_type=vegan),
        ])
        db.session.commit()
        return {"classic": classic.id, "vegan": vegan.id}


def test_cupcakes_requires_login(client):
    response = client.get("/cupcakes/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_cupcakes_list(client, login, cupcakes):
    login()
    response = client.get("/cupcakes/")
    assert response.status_code == 200
    assert b"Vanilla Dream" in response.data
    assert b"Berry Bliss" in response.data
    assert b"Vanilla sponge with buttercream" in response.data


def test_cupcakes_search(client, login, cupcakes):
    login()
    # Matches the description, case-insensitively
    response = client.get("/cupcakes/?q=RASPBERRY")
    assert b"Berry Bliss" in response.data
    assert b"Vanilla Dream" not in response.data


def test_cupcakes_filter_by_type(client, login, cupcakes):
    login()
    response = client.get(f"/cupcakes/?type={cupcakes['classic']}")
    assert b"Vanilla Dream" in response.data
    assert b"Berry Bliss" not in response.data


def test_cupcakes_invalid_type_shows_all(client, login, cupcakes):
    login()
    response = client.get("/cupcakes/?type=not-a-uuid")
    assert response.status_code == 200
    assert b"Vanilla Dream" in response.data
    assert b"Berry Bliss" in response.data


def test_nav_shows_cupcakes_link_when_logged_in(client, login):
    login()
    assert b'href="/cupcakes/"' in client.get("/profile/").data


# --- Add and edit (admin only)

def _type_id(app, name):
    with app.app_context():
        return CupcakeType.query.filter_by(name=name).one().id


def test_new_cupcake_forbidden_without_admin_role(client, login):
    login(roles=["user"])
    assert client.get("/cupcakes/new").status_code == 403
    assert client.post("/cupcakes/new", data={"name": "Sneaky"}).status_code == 403


def test_list_shows_add_and_edit_links_only_to_admin(client, login, cupcakes):
    login(roles=["user"])
    response = client.get("/cupcakes/")
    assert b"Add cupcake" not in response.data
    assert b"/edit" not in response.data

    login(roles=["admin"])
    response = client.get("/cupcakes/")
    assert b'href="/cupcakes/new"' in response.data
    assert b"/edit" in response.data


def test_create_cupcake(app, client, login):
    login(roles=["admin"])
    form = client.get("/cupcakes/new")
    assert form.status_code == 200
    assert b"Seasonal" in form.data

    response = client.post("/cupcakes/new", data={
        "name": "  Pumpkin Spice ",
        "type": str(_type_id(app, "Seasonal")),
        "description": "Autumn special",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Cupcake &#34;Pumpkin Spice&#34; added." in response.data
    with app.app_context():
        cupcake = Cupcake.query.filter_by(name="Pumpkin Spice").one()
        assert cupcake.cupcake_type.name == "Seasonal"
        assert cupcake.description == "Autumn special"


def test_create_cupcake_validation_errors(client, login):
    login(roles=["admin"])
    response = client.post("/cupcakes/new", data={"name": "", "type": "", "description": ""})
    assert response.status_code == 400
    assert b"Name is required." in response.data
    assert b"Choose a cupcake type." in response.data


def test_create_cupcake_with_unknown_type(client, login):
    login(roles=["admin"])
    response = client.post("/cupcakes/new", data={"name": "Mystery", "type": str(uuid.uuid4())})
    assert response.status_code == 400
    assert b"Choose a valid cupcake type." in response.data


def test_create_cupcake_with_existing_name(app, client, login, cupcakes):
    login(roles=["admin"])
    # The name check ignores case
    response = client.post("/cupcakes/new", data={"name": "vanilla dream", "type": str(cupcakes["classic"])})
    assert response.status_code == 400
    assert b"A cupcake with this name already exists." in response.data


def test_edit_cupcake(app, client, login):
    with app.app_context():
        cupcake = Cupcake(name="Lemon Drop", description="Lemon curd", cupcake_type_id=_type_id(app, "Classic"))
        db.session.add(cupcake)
        db.session.commit()
        cupcake_id = cupcake.id

    login(roles=["admin"])
    form = client.get(f"/cupcakes/{cupcake_id}/edit")
    assert form.status_code == 200
    assert b'value="Lemon Drop"' in form.data
    assert b"Lemon curd" in form.data

    response = client.post(f"/cupcakes/{cupcake_id}/edit", data={
        "name": "Lemon Drop",  # unchanged name is not a duplicate of itself
        "type": str(_type_id(app, "Gluten-free")),
        "description": "",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Cupcake &#34;Lemon Drop&#34; saved." in response.data
    with app.app_context():
        cupcake = db.session.get(Cupcake, cupcake_id)
        assert cupcake.cupcake_type.name == "Gluten-free"
        assert cupcake.description is None


def test_edit_cupcake_to_existing_name(client, login, cupcakes):
    login(roles=["admin"])
    with client.application.app_context():
        berry_id = Cupcake.query.filter_by(name="Berry Bliss").one().id
    response = client.post(f"/cupcakes/{berry_id}/edit",
                           data={"name": "Vanilla Dream", "type": str(cupcakes["vegan"])})
    assert response.status_code == 400
    assert b"A cupcake with this name already exists." in response.data


def test_edit_unknown_cupcake(client, login):
    login(roles=["admin"])
    assert client.get(f"/cupcakes/{uuid.uuid4()}/edit").status_code == 404

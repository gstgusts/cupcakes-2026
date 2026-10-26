import pytest

from app import db
from app.models import Cupcake, CupcakeType


@pytest.fixture(scope="module")
def cupcakes(app):
    """Two types with one cupcake each; returns the type ids."""
    with app.app_context():
        classic = CupcakeType(name="Classic")
        vegan = CupcakeType(name="Vegan")
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

import io
import uuid

import pytest

from app import db
from app.models import Cupcake, CupcakeImage, CupcakeType

# Only the first bytes decide the image type, so a PNG signature plus some bytes is enough
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture
def cupcake_id(app):
    """A new cupcake without images for each test."""
    with app.app_context():
        cupcake = Cupcake(name=f"Photo Cupcake {uuid.uuid4().hex[:8]}",
                          cupcake_type=CupcakeType.query.filter_by(name="Classic").one())
        db.session.add(cupcake)
        db.session.commit()
        return cupcake.id


def _upload(client, cupcake_id, data=PNG, description="", filename="cupcake.png", **kwargs):
    return client.post(f"/cupcakes/{cupcake_id}/images",
                       data={"image": (io.BytesIO(data), filename), "description": description},
                       content_type="multipart/form-data", **kwargs)


def _add_image(app, cupcake_id, description=None):
    with app.app_context():
        image = CupcakeImage(cupcake_id=cupcake_id, description=description, content_type="image/png", data=PNG)
        db.session.add(image)
        db.session.commit()
        return image.id


def test_upload_forbidden_without_admin_role(client, login, cupcake_id):
    login(roles=["user"])
    assert _upload(client, cupcake_id).status_code == 403


def test_upload_image(app, client, login, cupcake_id):
    login(roles=["admin"])
    response = _upload(client, cupcake_id, description="  Top view ", follow_redirects=True)

    assert response.status_code == 200
    assert b"Image added." in response.data
    assert b"Top view" in response.data
    with app.app_context():
        image = CupcakeImage.query.filter_by(cupcake_id=cupcake_id).one()
        assert image.description == "Top view"
        assert image.content_type == "image/png"
        assert image.data == PNG


def test_upload_several_images(app, client, login, cupcake_id):
    login(roles=["admin"])
    _upload(client, cupcake_id, description="First")
    _upload(client, cupcake_id, description="Second")
    with app.app_context():
        cupcake = db.session.get(Cupcake, cupcake_id)
        assert [image.description for image in cupcake.images] == ["First", "Second"]


def test_upload_type_comes_from_content_not_filename(client, login, cupcake_id):
    login(roles=["admin"])
    response = _upload(client, cupcake_id, data=b"<svg onload='alert(1)'></svg>", filename="cupcake.png")
    assert response.status_code == 400
    assert b"The image must be a JPEG, PNG, GIF or WebP file." in response.data


def test_upload_without_file(client, login, cupcake_id):
    login(roles=["admin"])
    response = client.post(f"/cupcakes/{cupcake_id}/images", data={"description": "Nothing"})
    assert response.status_code == 400
    assert b"Choose an image file." in response.data
    # The description is kept in the form
    assert b'value="Nothing"' in response.data


def test_upload_description_too_long(client, login, cupcake_id):
    login(roles=["admin"])
    response = _upload(client, cupcake_id, description="a" * 251)
    assert response.status_code == 400
    assert b"Description can be at most 250 characters." in response.data


def test_upload_image_too_large(client, login, cupcake_id):
    login(roles=["admin"])
    response = _upload(client, cupcake_id, data=PNG + b"\x00" * (2 * 1024 * 1024))
    assert response.status_code == 400
    assert b"The image can be at most 2 MB." in response.data


def test_upload_request_too_large(client, login, cupcake_id):
    login(roles=["admin"])
    # Larger than MAX_CONTENT_LENGTH: Flask rejects it before the view reads the file
    response = _upload(client, cupcake_id, data=PNG + b"\x00" * (4 * 1024 * 1024))
    assert response.status_code == 413
    assert b"The image can be at most 2 MB." in response.data


def test_show_image(app, client, login, cupcake_id):
    image_id = _add_image(app, cupcake_id)
    login(roles=["user"])
    response = client.get(f"/cupcakes/images/{image_id}")
    assert response.status_code == 200
    assert response.data == PNG
    assert response.headers["Content-Type"] == "image/png"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_show_image_requires_login(app, client, cupcake_id):
    image_id = _add_image(app, cupcake_id)
    response = client.get(f"/cupcakes/images/{image_id}")
    assert response.status_code == 302


def test_list_shows_first_image(app, client, login, cupcake_id):
    first_id = _add_image(app, cupcake_id, description="First photo")
    _add_image(app, cupcake_id, description="Second photo")
    login(roles=["user"])
    response = client.get("/cupcakes/")
    assert f'/cupcakes/images/{first_id}"'.encode() in response.data
    assert b'alt="First photo"' in response.data
    assert b"Second photo" not in response.data


def test_delete_image(app, client, login, cupcake_id):
    image_id = _add_image(app, cupcake_id)
    login(roles=["admin"])
    response = client.post(f"/cupcakes/{cupcake_id}/images/{image_id}/delete", follow_redirects=True)
    assert b"Image deleted." in response.data
    with app.app_context():
        assert db.session.get(CupcakeImage, image_id) is None


def test_delete_image_of_other_cupcake(app, client, login, cupcake_id):
    image_id = _add_image(app, cupcake_id)
    login(roles=["admin"])
    response = client.post(f"/cupcakes/{uuid.uuid4()}/images/{image_id}/delete")
    assert response.status_code == 404
    with app.app_context():
        assert db.session.get(CupcakeImage, image_id) is not None


def test_images_are_deleted_with_cupcake(app, cupcake_id):
    image_id = _add_image(app, cupcake_id)
    with app.app_context():
        db.session.delete(db.session.get(Cupcake, cupcake_id))
        db.session.commit()
        assert db.session.get(CupcakeImage, image_id) is None

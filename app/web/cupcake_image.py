from flask import Blueprint, abort, flash, redirect, request, url_for
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import RequestEntityTooLarge

from ..models import Cupcake, CupcakeImage
from ..models.base import db
from ..services.auth import login_required, role_required
from ..validations.cupcake_image import detect_image_type, validate_cupcake_image
from .cupcake import edit_page

cupcake_images_bp = Blueprint("cupcake_images", __name__, url_prefix="/cupcakes")


@cupcake_images_bp.get("/images/<uuid:image_id>")
@login_required
def show(image_id):
    """The image bytes from the database, with the content type detected at upload."""
    image = db.get_or_404(CupcakeImage, image_id)
    return image.data, {
        "Content-Type": image.content_type,
        # The browser must not guess another type from the content
        "X-Content-Type-Options": "nosniff",
        # An image never changes (a new upload gets a new id), so the browser may keep it
        "Cache-Control": "private, max-age=86400",
    }


@cupcake_images_bp.post("/<uuid:cupcake_id>/images")
@role_required("admin")
def upload(cupcake_id):
    cupcake = db.get_or_404(Cupcake, cupcake_id)
    file = request.files.get("image")
    data = file.read() if file else b""
    description = (request.form.get("description") or "").strip()

    errors = validate_cupcake_image(data, description)
    if errors:
        return edit_page(cupcake, 400, image_errors=errors, image_form={"description": description})

    cupcake.images.append(CupcakeImage(
        description=description or None,
        content_type=detect_image_type(data),
        data=data,
    ))
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return edit_page(cupcake, 500, image_form={"description": description},
                         error="Saving the image failed. Please try again.")

    flash("Image added.")
    return redirect(url_for("cupcakes.edit", cupcake_id=cupcake.id))


@cupcake_images_bp.post("/<uuid:cupcake_id>/images/<uuid:image_id>/delete")
@role_required("admin")
def delete(cupcake_id, image_id):
    image = db.get_or_404(CupcakeImage, image_id)
    if image.cupcake_id != cupcake_id:
        abort(404)
    db.session.delete(image)
    db.session.commit()
    flash("Image deleted.")
    return redirect(url_for("cupcakes.edit", cupcake_id=cupcake_id))


@cupcake_images_bp.errorhandler(RequestEntityTooLarge)
def too_large(e):
    # The upload is larger than MAX_CONTENT_LENGTH, so Flask stops reading it
    cupcake = db.get_or_404(Cupcake, request.view_args["cupcake_id"])
    return edit_page(cupcake, 413, image_errors={"image": "The image can be at most 2 MB."}, image_form={})

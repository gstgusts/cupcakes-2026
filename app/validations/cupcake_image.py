"""Validation of uploaded cupcake images."""

MAX_IMAGE_BYTES = 2 * 1024 * 1024


def detect_image_type(data):
    """Content type from the file's first bytes, or None if it is not an allowed image.

    The browser's content type and the file extension are not trusted. SVG is not allowed,
    because it can contain scripts.
    """
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_cupcake_image(data, description):
    """Checks the uploaded file (bytes) and its description."""
    errors = {}
    if not data:
        errors["image"] = "Choose an image file."
    elif len(data) > MAX_IMAGE_BYTES:
        errors["image"] = "The image can be at most 2 MB."
    elif detect_image_type(data) is None:
        errors["image"] = "The image must be a JPEG, PNG, GIF or WebP file."
    if len(description) > 250:
        errors["description"] = "Description can be at most 250 characters."
    return errors

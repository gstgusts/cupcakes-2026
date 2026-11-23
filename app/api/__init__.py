"""JSON API for the React and Vue apps (and the Flask pages): url prefix /api."""
from flask import Blueprint, jsonify, request

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.app_errorhandler(404)
@api_bp.app_errorhandler(405)
def routing_error(e):
    # Registered for the whole app, because an unknown URL or method is found before any blueprint runs:
    # JSON under /api, the normal error page everywhere else
    if request.path.startswith("/api/"):
        response = jsonify(error="Not found." if e.code == 404 else "Method not allowed.")
        response.status_code = e.code
        if e.code == 405:
            # Lists the allowed methods, as the normal 405 response does
            response.headers["Allow"] = ", ".join(e.valid_methods or [])
        return response
    return e


# The routes register themselves on api_bp (one module per entity, like app/web)
from . import docs, prediction, prediction_model  # noqa: E402,F401

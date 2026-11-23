"""API documentation: the OpenAPI description and a Swagger UI page to try the API.

Both are public (they contain no data); the API calls themselves still need a login.
"""
from pathlib import Path

from flask import render_template, send_file

from . import api_bp

OPENAPI_FILE = Path(__file__).with_name("openapi.yaml")


@api_bp.get("/openapi.yaml")
def openapi_spec():
    return send_file(OPENAPI_FILE, mimetype="application/yaml", max_age=0)


@api_bp.get("/docs")
def docs():
    return render_template("api/docs.html")

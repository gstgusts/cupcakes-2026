"""The OpenAPI description must match the API, so the docs cannot silently fall behind the code."""
import re
import uuid
from datetime import date
from decimal import Decimal

import pytest
import yaml

from app import db
from app.api.docs import OPENAPI_FILE
from app.models import Cupcake, CupcakeType, Prediction, PredictionModel, Store

# Documentation routes are not part of the API they describe
DOC_ROUTES = {"/api/openapi.yaml", "/api/docs"}
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@pytest.fixture(scope="module")
def spec():
    return yaml.safe_load(OPENAPI_FILE.read_text(encoding="utf-8"))


def _api_routes(app):
    """{(path, method)} of the API, with Flask's <converter:name> written as OpenAPI's {name}."""
    routes = set()
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/api/") and rule.rule not in DOC_ROUTES:
            path = re.sub(r"<(?:[^:<>]+:)?([^<>]+)>", r"{\1}", rule.rule)
            routes |= {(path, method.lower()) for method in rule.methods if method.lower() in HTTP_METHODS}
    return routes


def test_spec_is_served(client, spec):
    response = client.get("/api/openapi.yaml")
    assert response.status_code == 200
    assert response.mimetype == "application/yaml"
    assert yaml.safe_load(response.data) == spec
    assert spec["openapi"].startswith("3.")


def test_swagger_ui_page(client):
    # Public: the page and the description contain no data
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert b"swagger-ui-bundle.js" in response.data
    assert b'url: "/api/openapi.yaml"' in response.data


def test_every_api_route_is_documented(app, spec):
    documented = {(path, method) for path, item in spec["paths"].items() for method in item if method in HTTP_METHODS}
    routes = _api_routes(app)
    assert routes - documented == set(), "routes missing from openapi.yaml"
    assert documented - routes == set(), "openapi.yaml describes routes that do not exist"


def test_all_refs_exist(spec):
    refs = set()

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("$ref"), str):
                refs.add(node["$ref"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(spec)
    for ref in refs:
        target = spec
        for part in ref.removeprefix("#/").split("/"):
            assert part in target, f"{ref} does not exist"
            target = target[part]


@pytest.fixture
def prediction(app):
    """A model and a prediction, so the list endpoints return at least one item each."""
    with app.app_context():
        # Queries first: they flush the session, which must not happen with half-built objects
        cupcake_type = CupcakeType.query.filter_by(name="Classic").one()
        store = Store.query.filter_by(name="Riga Centre").one()
        cupcake = Cupcake(name=f"Docs Cupcake {uuid.uuid4().hex[:8]}", cupcake_type=cupcake_type)
        model = PredictionModel(name="Case 3", cupcake=cupcake, store=store,
                                average_demand=150, demand_std_dev=30, production_cost=Decimal("10"),
                                selling_price=Decimal("15"), salvage_value=Decimal("2"))
        db.session.add(Prediction(prediction_model=model, date=date(2028, 1, 1), recommended_quantity=141))
        db.session.commit()


@pytest.mark.parametrize("url, schema", [
    ("/api/prediction-models", "PredictionModel"),
    ("/api/predictions", "Prediction"),
])
def test_responses_match_schemas(client, login, spec, prediction, url, schema):
    login()
    item = client.get(url).json[0]
    properties = spec["components"]["schemas"][schema]["properties"]
    assert set(item) == set(properties), f"{url} fields differ from the {schema} schema"

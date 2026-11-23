from datetime import date

from app.commands.seed_demo import CUPCAKES, PREDICTION_DAYS, PREDICTION_MODELS
from app.models import Cupcake, Prediction, PredictionModel, Store


def _run(app):
    result = app.test_cli_runner().invoke(args=["seed-demo"])
    assert result.exit_code == 0, result.output
    return result.output


def test_seed_demo_adds_data_and_can_run_again(app):
    first = _run(app)
    assert first.startswith("Added ")

    with app.app_context():
        names = [name for name, _, _ in CUPCAKES]
        assert Cupcake.query.filter(Cupcake.name.in_(names)).count() == len(CUPCAKES)

        case_3 = (PredictionModel.query.join(PredictionModel.cupcake).join(PredictionModel.store)
                  .filter(Cupcake.name == "Vanilla Bean", Store.name == "Riga Centre",
                          PredictionModel.name == "Case 3").one())
        predictions = Prediction.query.filter_by(prediction_model_id=case_3.id).all()
        assert len(predictions) == PREDICTION_DAYS
        assert min(p.date for p in predictions) == date.today()
        # The lecture example: bake 141
        assert {p.recommended_quantity for p in predictions} == {141}

        models = PredictionModel.query.filter(PredictionModel.cupcake.has(Cupcake.name.in_(names))).count()
        assert models == len(PREDICTION_MODELS)

    # Running it again adds nothing
    assert _run(app) == "Added 0 cupcakes, 0 prediction models, 0 predictions.\n"

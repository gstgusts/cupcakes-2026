import uuid

from app.models.base import db


class Prediction(db.Model):
    """Recommended number of cupcakes to bake on one date, calculated from a prediction model."""
    __tablename__ = "predictions"
    id = db.Column(
        db.Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    # No separate index: the unique constraint below starts with this column and serves as its index
    prediction_model_id = db.Column(
        db.Uuid,
        db.ForeignKey("prediction_models.id", ondelete="RESTRICT"),
        nullable=False,
    )
    date = db.Column(db.Date, nullable=False)
    recommended_quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    prediction_model = db.relationship("PredictionModel", back_populates="predictions")
    # At most one plan, because a plan is unique per cupcake, store and date (ON DELETE RESTRICT)
    plans = db.relationship("Plan", back_populates="prediction", passive_deletes="all")

    __table_args__ = (
        # One prediction per model and date
        db.UniqueConstraint("prediction_model_id", "date", name="predictions_prediction_model_id_date_key"),
        db.CheckConstraint("recommended_quantity >= 0", name="recommended_quantity"),
    )

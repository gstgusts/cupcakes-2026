import uuid

from app.models.base import db


class Plan(db.Model):
    """Number of cupcakes a user confirmed to bake for one date, cupcake and store.

    The cupcake, store and date are the ones of the prediction the plan is based on.
    """
    __tablename__ = "plans"
    id = db.Column(
        db.Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    date = db.Column(db.Date, nullable=False)
    # No separate index: the unique constraint below starts with this column and serves as its index
    cupcake_id = db.Column(
        db.Uuid,
        db.ForeignKey("cupcakes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    store_id = db.Column(
        db.Uuid,
        db.ForeignKey("stores.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    prediction_id = db.Column(
        db.Uuid,
        db.ForeignKey("predictions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity_confirmed = db.Column(db.Integer, nullable=False)
    confirmed_by_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    confirmed_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    cupcake = db.relationship("Cupcake")
    store = db.relationship("Store")
    prediction = db.relationship("Prediction", back_populates="plans")
    confirmed_by = db.relationship("User")
    # The daily sales summary, once recorded (ON DELETE RESTRICT)
    sales = db.relationship("Sales", back_populates="plan", uselist=False, passive_deletes="all")

    __table_args__ = (
        # One plan per cupcake, store and date
        db.UniqueConstraint("cupcake_id", "store_id", "date", name="plans_cupcake_id_store_id_date_key"),
        db.CheckConstraint("quantity_confirmed >= 0", name="quantity_confirmed"),
    )

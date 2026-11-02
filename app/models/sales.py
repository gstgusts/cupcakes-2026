import uuid

from app.models.base import db


class Sales(db.Model):
    """Daily sales summary of one plan. The cupcake and store are identified through the plan."""
    __tablename__ = "sales"
    id = db.Column(
        db.Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    # One summary per plan; the unique constraint also serves as the index of the foreign key
    plan_id = db.Column(
        db.Uuid,
        db.ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    # The plan's date (the day the cupcakes were sold)
    date = db.Column(db.Date, nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    # Sales income, not profit
    revenue = db.Column(db.Numeric(10, 2), nullable=False)
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    plan = db.relationship("Plan", back_populates="sales")

    __table_args__ = (
        db.CheckConstraint("quantity_sold >= 0", name="quantity_sold"),
        db.CheckConstraint("revenue >= 0", name="revenue"),
    )

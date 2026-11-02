import uuid

from app.models.base import db


class PredictionModel(db.Model):
    """Newsvendor parameters for one cupcake at one store.

    Demand variability is the standard deviation of daily demand.
    """
    __tablename__ = "prediction_models"
    id = db.Column(
        db.Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    name = db.Column(db.String(100), nullable=False)
    cupcake_id = db.Column(
        db.Uuid,
        db.ForeignKey("cupcakes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    store_id = db.Column(
        db.Uuid,
        db.ForeignKey("stores.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Cupcakes per day
    average_demand = db.Column(db.Float, nullable=False)
    demand_std_dev = db.Column(db.Float, nullable=False)
    # Money per cupcake
    production_cost = db.Column(db.Numeric(10, 2), nullable=False)
    selling_price = db.Column(db.Numeric(10, 2), nullable=False)
    salvage_value = db.Column(db.Numeric(10, 2), nullable=False)

    cupcake = db.relationship("Cupcake", back_populates="prediction_models")
    store = db.relationship("Store", back_populates="prediction_models")

    # Both costs must be positive, otherwise the critical ratio is not defined:
    # underage cost = price - cost > 0, overage cost = cost - salvage > 0
    __table_args__ = (
        db.CheckConstraint("average_demand >= 0", name="average_demand"),
        db.CheckConstraint("demand_std_dev >= 0", name="demand_std_dev"),
        db.CheckConstraint("salvage_value >= 0", name="salvage_value"),
        db.CheckConstraint("salvage_value < production_cost", name="salvage_below_cost"),
        db.CheckConstraint("production_cost < selling_price", name="cost_below_price"),
    )

    @property
    def underage_cost(self):
        """Cu = p - c: profit lost on each sale we miss because we baked too few."""
        return self.selling_price - self.production_cost

    @property
    def overage_cost(self):
        """Co = c - s: loss on each cupcake left over because we baked too many."""
        return self.production_cost - self.salvage_value

    @property
    def critical_ratio(self):
        """CR = Cu / (Cu + Co): bake so that P(demand <= quantity) equals this."""
        return float(self.underage_cost / (self.underage_cost + self.overage_cost))

import uuid

from app.models.base import db


class Store(db.Model):
    __tablename__ = "stores"
    id = db.Column(
        db.Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    name = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=False)
    # A store cannot be deleted while prediction models use it (ON DELETE RESTRICT in the database)
    prediction_models = db.relationship("PredictionModel", back_populates="store", passive_deletes="all")

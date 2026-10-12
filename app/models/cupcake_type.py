import uuid

from app.models.base import db


class CupcakeType(db.Model):
    __tablename__ = "cupcake_types"
    id = db.Column(
        db.Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    name = db.Column(db.String(100), nullable=False, unique=True)
    # A type cannot be deleted while cupcakes use it (ON DELETE RESTRICT in the database)
    cupcakes = db.relationship("Cupcake", back_populates="cupcake_type", passive_deletes="all")

import uuid

from app.models.base import db


class Cupcake(db.Model):
    __tablename__ = "cupcakes"
    id = db.Column(
        db.Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    # PostgreSQL does not index foreign keys automatically, so the index is explicit
    cupcake_type_id = db.Column(
        db.Uuid,
        db.ForeignKey("cupcake_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cupcake_type = db.relationship("CupcakeType", back_populates="cupcakes")

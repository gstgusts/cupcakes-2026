import uuid

from app.models.base import db


class CupcakeImage(db.Model):
    __tablename__ = "cupcake_images"
    id = db.Column(
        db.Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    # Images belong to the cupcake and are deleted with it
    cupcake_id = db.Column(
        db.Uuid,
        db.ForeignKey("cupcakes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description = db.Column(db.String(250))
    content_type = db.Column(db.String(50), nullable=False)
    # Deferred: the image bytes are loaded only when accessed, not with every list query
    data = db.deferred(db.Column(db.LargeBinary, nullable=False))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    cupcake = db.relationship("Cupcake", back_populates="images")

import uuid

from app.models.base import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(
        db.Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    # Links the Keycloak account to this profile (matched case-insensitively)
    email = db.Column(db.String(255), nullable=False)

    __table_args__ = (
        db.Index("ux_users_email_lower", db.func.lower(email), unique=True),
    )

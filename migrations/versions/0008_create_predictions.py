"""create predictions table

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "predictions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("prediction_model_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("recommended_quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="predictions_pkey"),
        sa.ForeignKeyConstraint(
            ["prediction_model_id"], ["prediction_models.id"],
            name="predictions_prediction_model_id_fkey", ondelete="RESTRICT",
        ),
        # Also serves as the index of the foreign key (its first column)
        sa.UniqueConstraint("prediction_model_id", "date", name="predictions_prediction_model_id_date_key"),
        # op.f(): the name is final, the naming convention must not be applied again
        sa.CheckConstraint("recommended_quantity >= 0", name=op.f("predictions_recommended_quantity_check")),
    )


def downgrade():
    op.drop_table("predictions")

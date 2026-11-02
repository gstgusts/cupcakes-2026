"""create plans table

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plans",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("cupcake_id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column("prediction_id", sa.Uuid(), nullable=False),
        sa.Column("quantity_confirmed", sa.Integer(), nullable=False),
        sa.Column("confirmed_by_id", sa.Uuid(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="plans_pkey"),
        sa.ForeignKeyConstraint(
            ["cupcake_id"], ["cupcakes.id"],
            name="plans_cupcake_id_fkey", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["store_id"], ["stores.id"],
            name="plans_store_id_fkey", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["prediction_id"], ["predictions.id"],
            name="plans_prediction_id_fkey", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by_id"], ["users.id"],
            name="plans_confirmed_by_id_fkey", ondelete="RESTRICT",
        ),
        # Also serves as the index of cupcake_id (its first column)
        sa.UniqueConstraint("cupcake_id", "store_id", "date", name="plans_cupcake_id_store_id_date_key"),
        # op.f(): the name is final, the naming convention must not be applied again
        sa.CheckConstraint("quantity_confirmed >= 0", name=op.f("plans_quantity_confirmed_check")),
    )
    op.create_index("plans_store_id_idx", "plans", ["store_id"])
    op.create_index("plans_prediction_id_idx", "plans", ["prediction_id"])
    op.create_index("plans_confirmed_by_id_idx", "plans", ["confirmed_by_id"])


def downgrade():
    op.drop_index("plans_confirmed_by_id_idx", table_name="plans")
    op.drop_index("plans_prediction_id_idx", table_name="plans")
    op.drop_index("plans_store_id_idx", table_name="plans")
    op.drop_table("plans")

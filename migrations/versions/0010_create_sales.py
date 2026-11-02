"""create sales table

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sales",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("quantity_sold", sa.Integer(), nullable=False),
        sa.Column("revenue", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="sales_pkey"),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"],
            name="sales_plan_id_fkey", ondelete="RESTRICT",
        ),
        # One summary per plan; also serves as the index of the foreign key
        sa.UniqueConstraint("plan_id", name="sales_plan_id_key"),
        # op.f(): the names are final, the naming convention must not be applied again
        sa.CheckConstraint("quantity_sold >= 0", name=op.f("sales_quantity_sold_check")),
        sa.CheckConstraint("revenue >= 0", name=op.f("sales_revenue_check")),
    )


def downgrade():
    op.drop_table("sales")

"""create stores and prediction_models tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stores",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name="stores_pkey"),
        sa.UniqueConstraint("name", name="stores_name_key"),
    )
    op.create_table(
        "prediction_models",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("cupcake_id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column("average_demand", sa.Float(), nullable=False),
        sa.Column("demand_std_dev", sa.Float(), nullable=False),
        sa.Column("production_cost", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("selling_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("salvage_value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id", name="prediction_models_pkey"),
        sa.ForeignKeyConstraint(
            ["cupcake_id"], ["cupcakes.id"],
            name="prediction_models_cupcake_id_fkey", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["store_id"], ["stores.id"],
            name="prediction_models_store_id_fkey", ondelete="RESTRICT",
        ),
        # op.f(): the names are final, the naming convention must not be applied again
        sa.CheckConstraint("average_demand >= 0", name=op.f("prediction_models_average_demand_check")),
        sa.CheckConstraint("demand_std_dev >= 0", name=op.f("prediction_models_demand_std_dev_check")),
        sa.CheckConstraint("salvage_value >= 0", name=op.f("prediction_models_salvage_value_check")),
        sa.CheckConstraint("salvage_value < production_cost", name=op.f("prediction_models_salvage_below_cost_check")),
        sa.CheckConstraint("production_cost < selling_price", name=op.f("prediction_models_cost_below_price_check")),
    )
    op.create_index("prediction_models_cupcake_id_idx", "prediction_models", ["cupcake_id"])
    op.create_index("prediction_models_store_id_idx", "prediction_models", ["store_id"])


def downgrade():
    op.drop_index("prediction_models_store_id_idx", table_name="prediction_models")
    op.drop_index("prediction_models_cupcake_id_idx", table_name="prediction_models")
    op.drop_table("prediction_models")
    op.drop_table("stores")

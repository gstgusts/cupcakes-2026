"""create cupcake_types and cupcakes tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cupcake_types",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id", name="cupcake_types_pkey"),
        sa.UniqueConstraint("name", name="cupcake_types_name_key"),
    )
    op.create_table(
        "cupcakes",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cupcake_type_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="cupcakes_pkey"),
        sa.UniqueConstraint("name", name="cupcakes_name_key"),
        sa.ForeignKeyConstraint(
            ["cupcake_type_id"], ["cupcake_types.id"],
            name="cupcakes_cupcake_type_id_fkey", ondelete="RESTRICT",
        ),
    )
    op.create_index("cupcakes_cupcake_type_id_idx", "cupcakes", ["cupcake_type_id"])


def downgrade():
    op.drop_index("cupcakes_cupcake_type_id_idx", table_name="cupcakes")
    op.drop_table("cupcakes")
    op.drop_table("cupcake_types")

"""create cupcake_images table

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cupcake_images",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cupcake_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.String(length=250), nullable=True),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="cupcake_images_pkey"),
        sa.ForeignKeyConstraint(
            ["cupcake_id"], ["cupcakes.id"],
            name="cupcake_images_cupcake_id_fkey", ondelete="CASCADE",
        ),
    )
    op.create_index("cupcake_images_cupcake_id_idx", "cupcake_images", ["cupcake_id"])


def downgrade():
    op.drop_index("cupcake_images_cupcake_id_idx", table_name="cupcake_images")
    op.drop_table("cupcake_images")

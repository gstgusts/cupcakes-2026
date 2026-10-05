"""create users table

Revision ID: 0001
Revises:
Create Date: 2026-10-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("surname", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # Unique regardless of letter case, since users are matched by email case-insensitively
    op.create_index("ux_users_email_lower", "users", [sa.text("lower(email)")], unique=True)


def downgrade():
    op.drop_index("ux_users_email_lower", table_name="users")
    op.drop_table("users")

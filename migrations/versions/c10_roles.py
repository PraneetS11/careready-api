"""Add account roles and activation with safe defaults for existing rows."""

import sqlalchemy as sa
from alembic import op

revision = "c10_roles"
down_revision = "c8af9d233c2f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user", sa.Column("role", sa.String(), nullable=False, server_default="coordinator")
    )
    op.add_column(
        "user", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true())
    )


def downgrade():
    op.drop_column("user", "is_active")
    op.drop_column("user", "role")

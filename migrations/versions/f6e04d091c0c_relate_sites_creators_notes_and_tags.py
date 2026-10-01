"""relate sites creators notes and tags

Revision ID: f6e04d091c0c
Revises: c10_roles
Create Date: 2026-10-01 13:25:40.144002

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6e04d091c0c"
down_revision: Union[str, Sequence[str], None] = "c10_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sitetag",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "sitenote",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("site_id", sa.Uuid(), nullable=False),
        sa.Column("author_user_id", sa.Uuid(), nullable=False),
        sa.Column("text", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["site_id"], ["site.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sitetaglink",
        sa.Column("site_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["site.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["sitetag.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("site_id", "tag_id"),
    )
    op.add_column("site", sa.Column("created_by_user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "site_created_by_user_id_fkey",
        "site",
        "user",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("site_created_by_user_id_fkey", "site", type_="foreignkey")
    op.drop_column("site", "created_by_user_id")
    op.drop_table("sitetaglink")
    op.drop_table("sitenote")
    op.drop_table("sitetag")

"""Add scoped care network profiles, visits and equipment."""

import sqlalchemy as sa
from alembic import op

revision = "n01_care_network"
down_revision = "f6e04d091c0c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agency",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("user.id"), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
    )
    op.create_table(
        "careprofile",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("user.id"), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("agency_id", sa.Uuid(), sa.ForeignKey("agency.id")),
        sa.Column("experience", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(), nullable=False),
        sa.Column("services", sa.JSON(), nullable=False),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_careprofile_agency_id", "careprofile", ["agency_id"])
    op.create_table(
        "carevisit",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("series_id", sa.Uuid(), nullable=False),
        sa.Column("agency_id", sa.Uuid(), sa.ForeignKey("agency.id"), nullable=False),
        sa.Column("requester_id", sa.Uuid(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("user.id")),
        *[
            sa.Column(x, sa.String(), nullable=False)
            for x in [
                "service",
                "recipient",
                "address",
                "city",
                "timezone",
                "gender_preference",
                "status",
                "notes",
                "preferred_language",
                "communication",
            ]
        ],
        sa.Column("smoke_free", sa.Boolean(), nullable=False),
        sa.Column("pets_present", sa.Boolean(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("min_experience", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "duration_minutes >= 30 AND duration_minutes <= 240", name="visit_duration_bounds"
        ),
        sa.CheckConstraint("min_experience BETWEEN 0 AND 3", name="visit_experience_bounds"),
    )
    for col in ("series_id", "agency_id", "requester_id", "provider_id"):
        op.create_index("ix_carevisit_" + col, "carevisit", [col])
    op.create_table(
        "caredevice",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("agency_id", sa.Uuid(), sa.ForeignKey("agency.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("asset_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.UniqueConstraint("agency_id", "asset_code", name="device_agency_asset_unique"),
    )
    op.create_index("ix_caredevice_agency_id", "caredevice", ["agency_id"])
    op.create_table(
        "careevent",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("visit_id", sa.Uuid(), sa.ForeignKey("carevisit.id"), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_careevent_visit_id", "careevent", ["visit_id"])


def downgrade():
    for table in ("careevent", "caredevice", "carevisit", "careprofile", "agency"):
        op.drop_table(table)

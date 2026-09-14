"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostGIS must be enabled before any geography columns are created.
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    user_role = postgresql.ENUM("USER", "ADMIN", name="user_role")
    user_role.create(op.get_bind(), checkfirst=True)

    source_type = postgresql.ENUM(
        "citizen", "weather_api", "government", "news", "public_feed", "simulated_social",
        name="source_type",
    )
    source_type.create(op.get_bind(), checkfirst=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM("USER", "ADMIN", name="user_role", create_type=False), nullable=False, server_default="USER"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- sources ---
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "citizen", "weather_api", "government", "news", "public_feed", "simulated_social",
                name="source_type", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("reliability_score", sa.Float(), nullable=False, server_default="50.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_sources"),
        sa.UniqueConstraint("name", name="uq_sources_name"),
    )

    # --- incidents (created before reports, since reports FK to incidents) ---
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location", geoalchemy2.Geography(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("state", sa.String(120), nullable=True),
        sa.Column("district", sa.String(120), nullable=True),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("report_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("suspicious_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_incidents_latitude_range"),
        sa.CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_incidents_longitude_range"),
        sa.CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="ck_incidents_confidence_range"),
        sa.PrimaryKeyConstraint("id", name="pk_incidents"),
    )
    op.create_index("ix_incidents_event_type", "incidents", ["event_type"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_start_time", "incidents", ["start_time"])
    # NOTE: GeoAlchemy2 automatically creates a GIST spatial index (idx_incidents_location)
    # on Geography columns when the table is created, so no explicit index is added here.

    # --- reports ---
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=True),
        sa.Column("event_confidence", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location", geoalchemy2.Geography(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("district", sa.String(120), nullable=True),
        sa.Column("state", sa.String(120), nullable=True),
        sa.Column("media_url", sa.String(512), nullable=True),
        sa.Column("report_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_reports_latitude_range"),
        sa.CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_reports_longitude_range"),
        sa.CheckConstraint(
            "event_confidence IS NULL OR (event_confidence >= 0 AND event_confidence <= 1)",
            name="ck_reports_event_confidence_range",
        ),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="fk_reports_source_id_sources", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], name="fk_reports_incident_id_incidents", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_reports"),
    )
    op.create_index("ix_reports_source_id", "reports", ["source_id"])
    op.create_index("ix_reports_incident_id", "reports", ["incident_id"])
    op.create_index("ix_reports_timestamp", "reports", ["timestamp"])
    op.create_index("ix_reports_event_type", "reports", ["event_type"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_state", "reports", ["state"])
    op.create_index("ix_reports_city", "reports", ["city"])
    # NOTE: GeoAlchemy2 automatically creates a GIST spatial index (idx_reports_location)
    # on Geography columns when the table is created, so no explicit index is added here.

    # --- verifications ---
    op.create_table(
        "verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trust_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="NEEDS_REVIEW"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("trust_score >= 0 AND trust_score <= 100", name="ck_verifications_trust_score_range"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], name="fk_verifications_report_id_reports", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], name="fk_verifications_verified_by_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_verifications"),
    )
    op.create_index("ix_verifications_report_id", "verifications", ["report_id"], unique=True)
    op.create_index("ix_verifications_status", "verifications", ["status"])

    # --- duplicates ---
    op.create_table(
        "duplicates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("master_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("similarity_score >= 0 AND similarity_score <= 1", name="ck_duplicates_similarity_score_range"),
        sa.CheckConstraint("report_id != master_report_id", name="ck_duplicates_duplicate_not_self"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], name="fk_duplicates_report_id_reports", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["master_report_id"], ["reports.id"], name="fk_duplicates_master_report_id_reports", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_duplicates"),
    )
    op.create_index("ix_duplicates_report_id", "duplicates", ["report_id"], unique=True)
    op.create_index("ix_duplicates_master_report_id", "duplicates", ["master_report_id"])


def downgrade() -> None:
    op.drop_table("duplicates")
    op.drop_table("verifications")
    op.drop_index("idx_reports_location", table_name="reports")
    op.drop_table("reports")
    op.drop_index("idx_incidents_location", table_name="incidents")
    op.drop_table("incidents")
    op.drop_table("sources")
    op.drop_table("users")

    postgresql.ENUM(name="source_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="user_role").drop(op.get_bind(), checkfirst=True)

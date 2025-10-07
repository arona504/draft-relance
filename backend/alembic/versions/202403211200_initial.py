"""Initial schema with RLS."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "202403211200"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    slot_mode_enum = sa.Enum("onsite", "tele", name="slot_mode")
    slot_status_enum = sa.Enum("open", "closed", name="slot_status")
    appointment_status_enum = sa.Enum("booked", "cancelled", name="appointment_status")
    appointment_mode_enum = sa.Enum("onsite", "tele", name="appointment_mode")

    slot_mode_enum.create(op.get_bind(), checkfirst=True)
    slot_status_enum.create(op.get_bind(), checkfirst=True)
    appointment_status_enum.create(op.get_bind(), checkfirst=True)
    appointment_mode_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "calendars",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("practitioner_id", sa.String(length=36), nullable=False),
    )
    op.create_index("ix_calendars_tenant_id", "calendars", ["tenant_id"])
    op.create_index("ix_calendars_practitioner_id", "calendars", ["practitioner_id"])

    op.create_table(
        "slots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("calendar_id", sa.String(length=36), sa.ForeignKey("calendars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("mode", slot_mode_enum, nullable=False),
        sa.Column("status", slot_status_enum, nullable=False),
        sa.UniqueConstraint("calendar_id", "starts_at", name="uq_slot_calendar_starts"),
    )
    op.create_index("ix_slots_tenant_id", "slots", ["tenant_id"])
    op.create_index("ix_slots_starts_at", "slots", ["starts_at"])
    op.create_index("ix_slots_ends_at", "slots", ["ends_at"])
    op.create_index("ix_slots_status", "slots", ["status"])

    op.create_table(
        "appointments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("slot_id", sa.String(length=36), sa.ForeignKey("slots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("status", appointment_status_enum, nullable=False, server_default="booked"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("mode", appointment_mode_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_appointments_tenant_id", "appointments", ["tenant_id"])
    op.create_index("ix_appointments_slot_id", "appointments", ["slot_id"])
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_status", "appointments", ["status"])

    op.create_table(
        "patient_access_grants",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("resource_tenant_id", sa.String(length=36), nullable=False),
        sa.Column("granted_tenant_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("read_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_pag_resource_tenant", "patient_access_grants", ["resource_tenant_id"])
    op.create_index("ix_pag_granted_tenant", "patient_access_grants", ["granted_tenant_id"])
    op.create_index("ix_pag_patient", "patient_access_grants", ["patient_id"])

    for table in ("calendars", "slots", "appointments"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = current_setting('app.tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
            """
        )

    op.execute("ALTER TABLE patient_access_grants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE patient_access_grants FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON patient_access_grants
        USING (
            resource_tenant_id = current_setting('app.tenant_id', true)
            OR granted_tenant_id = current_setting('app.tenant_id', true)
        )
        WITH CHECK (resource_tenant_id = current_setting('app.tenant_id', true));
        """
    )

    op.execute(
        """
        -- Cross-tenant read policy skeleton leveraging patient_access_grants for read-only bundles
        CREATE POLICY appointment_grant_read ON appointments
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1
                FROM patient_access_grants pag
                WHERE pag.granted_tenant_id = current_setting('app.tenant_id', true)
                  AND pag.resource_tenant_id = appointments.tenant_id
                  AND pag.read_only = true
            )
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS appointment_grant_read ON appointments")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON patient_access_grants")
    op.execute("ALTER TABLE patient_access_grants DISABLE ROW LEVEL SECURITY")

    for table in ("appointments", "slots", "calendars"):
        op.execute("DROP POLICY IF EXISTS tenant_isolation ON {table}".format(table=table))
        op.execute("ALTER TABLE {table} DISABLE ROW LEVEL SECURITY".format(table=table))

    op.drop_index("ix_pag_patient", table_name="patient_access_grants")
    op.drop_index("ix_pag_granted_tenant", table_name="patient_access_grants")
    op.drop_index("ix_pag_resource_tenant", table_name="patient_access_grants")
    op.drop_table("patient_access_grants")

    op.drop_index("ix_appointments_status", table_name="appointments")
    op.drop_index("ix_appointments_patient_id", table_name="appointments")
    op.drop_index("ix_appointments_slot_id", table_name="appointments")
    op.drop_index("ix_appointments_tenant_id", table_name="appointments")
    op.drop_table("appointments")
    op.drop_index("ix_slots_status", table_name="slots")
    op.drop_index("ix_slots_ends_at", table_name="slots")
    op.drop_index("ix_slots_starts_at", table_name="slots")
    op.drop_index("ix_slots_tenant_id", table_name="slots")
    op.drop_table("slots")
    op.drop_index("ix_calendars_practitioner_id", table_name="calendars")
    op.drop_index("ix_calendars_tenant_id", table_name="calendars")
    op.drop_table("calendars")

    appointment_mode_enum = sa.Enum("onsite", "tele", name="appointment_mode")
    appointment_status_enum = sa.Enum("booked", "cancelled", name="appointment_status")
    slot_status_enum = sa.Enum("open", "closed", name="slot_status")
    slot_mode_enum = sa.Enum("onsite", "tele", name="slot_mode")

    appointment_mode_enum.drop(op.get_bind(), checkfirst=True)
    appointment_status_enum.drop(op.get_bind(), checkfirst=True)
    slot_status_enum.drop(op.get_bind(), checkfirst=True)
    slot_mode_enum.drop(op.get_bind(), checkfirst=True)

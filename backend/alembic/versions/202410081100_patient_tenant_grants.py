"""Add patient_tenant_grants table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "202410081100"
down_revision = "202403211200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_tenant_grants",
        sa.Column("patient_user_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False, server_default="appointments"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.execute("ALTER TABLE patient_tenant_grants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE patient_tenant_grants FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_grant_isolation ON patient_tenant_grants
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_grant_isolation ON patient_tenant_grants")
    op.execute("ALTER TABLE patient_tenant_grants DISABLE ROW LEVEL SECURITY")
    op.drop_table("patient_tenant_grants")

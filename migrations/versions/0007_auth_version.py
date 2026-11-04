"""Add authentication token version for revoking old sessions."""
from alembic import op
import sqlalchemy as sa

revision = "0007_auth_version"
down_revision = "0006_notifications"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("auth_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("users", "auth_version", existing_type=sa.Integer(), server_default=None)

def downgrade() -> None:
    op.drop_column("users", "auth_version")

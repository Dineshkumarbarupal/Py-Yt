"""Add profile fields to users."""
from alembic import op
import sqlalchemy as sa

revision = "0005_user_profile"
down_revision = "0004_watch_later"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=False, server_default=""))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=2048), nullable=True))
    op.alter_column("users", "bio", server_default=None)

def downgrade() -> None:
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "bio")

"""Add profile fields to users."""
from alembic import op
import sqlalchemy as sa

revision = "0005_user_profile"
down_revision = "0004_watch_later"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # MySQL does not permit a default on TEXT columns. Add nullable,
    # backfill existing rows, then enforce NOT NULL.
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.execute("UPDATE users SET bio = '' WHERE bio IS NULL")
    op.alter_column("users", "bio", existing_type=sa.Text(), nullable=False)
    op.add_column("users", sa.Column("avatar_url", sa.String(length=2048), nullable=True))

def downgrade() -> None:
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "bio")

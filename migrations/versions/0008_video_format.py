"""Add standard and short video format metadata."""
from alembic import op
import sqlalchemy as sa

revision = "0008_video_format"
down_revision = "0007_auth_version"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        "videos",
        sa.Column("video_format", sa.String(length=20), nullable=False, server_default="standard"),
    )
    op.alter_column("videos", "video_format", existing_type=sa.String(length=20), server_default=None)

def downgrade() -> None:
    op.drop_column("videos", "video_format")

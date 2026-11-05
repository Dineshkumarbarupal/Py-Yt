"""Add custom thumbnail storage key to videos."""
from alembic import op
import sqlalchemy as sa

revision = "0010_video_thumbnails"
down_revision = "0009_content_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "videos",
        sa.Column("thumbnail_storage_key", sa.String(length=700), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("videos", "thumbnail_storage_key")

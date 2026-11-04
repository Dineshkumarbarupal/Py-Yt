"""Add object-storage metadata to videos."""
from alembic import op
import sqlalchemy as sa

revision = "0003_video_storage"
down_revision = "0002_video_category"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("videos", sa.Column("storage_key", sa.String(length=1024), nullable=True))
    op.add_column("videos", sa.Column("mime_type", sa.String(length=120), nullable=True))
    op.add_column("videos", sa.Column("file_size_bytes", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_videos_storage_key", "videos", ["storage_key"])

def downgrade() -> None:
    op.drop_constraint("uq_videos_storage_key", "videos", type_="unique")
    op.drop_column("videos", "file_size_bytes")
    op.drop_column("videos", "mime_type")
    op.drop_column("videos", "storage_key")

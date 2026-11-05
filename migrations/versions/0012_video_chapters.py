"""Create video chapter markers."""
from alembic import op
import sqlalchemy as sa

revision = "0012_video_chapters"
down_revision = "0011_video_captions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_chapters",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "video_id",
            sa.String(length=36),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("start_seconds", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("video_id", "start_seconds", name="uq_video_chapter_start"),
    )
    op.create_index("ix_video_chapters_video_id", "video_chapters", ["video_id"])


def downgrade() -> None:
    op.drop_index("ix_video_chapters_video_id", table_name="video_chapters")
    op.drop_table("video_chapters")

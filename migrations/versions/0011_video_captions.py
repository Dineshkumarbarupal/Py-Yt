"""Create per-video WebVTT caption tracks."""
from alembic import op
import sqlalchemy as sa

revision = "0011_video_captions"
down_revision = "0010_video_thumbnails"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_captions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "video_id",
            sa.String(length=36),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("vtt_content", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("video_id", "language", name="uq_video_caption_language"),
    )
    op.create_index("ix_video_captions_video_id", "video_captions", ["video_id"])
    op.alter_column("video_captions", "is_default", existing_type=sa.Boolean(), server_default=None)


def downgrade() -> None:
    op.drop_index("ix_video_captions_video_id", table_name="video_captions")
    op.drop_table("video_captions")

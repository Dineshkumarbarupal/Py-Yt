"""Create Watch Later library table."""
from alembic import op
import sqlalchemy as sa

revision = "0004_watch_later"
down_revision = "0003_video_storage"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "watch_later",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("video_id", sa.String(length=36), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "video_id", name="uq_user_watch_later"),
    )
    op.create_index("ix_watch_later_user_id", "watch_later", ["user_id"])
    op.create_index("ix_watch_later_video_id", "watch_later", ["video_id"])

def downgrade() -> None:
    op.drop_table("watch_later")

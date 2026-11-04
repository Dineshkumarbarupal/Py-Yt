"""Add content reports and moderation metadata."""
from alembic import op
import sqlalchemy as sa

revision = "0009_content_reports"
down_revision = "0008_video_format"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "content_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("reporter_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("resolution_note", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("reporter_id", "target_type", "target_id", name="uq_reporter_target"),
    )
    op.create_index("ix_content_reports_reporter_id", "content_reports", ["reporter_id"])
    op.create_index("ix_content_reports_reviewer_id", "content_reports", ["reviewer_id"])
    op.create_index("ix_content_reports_status_created", "content_reports", ["status", "created_at"])
    op.create_index("ix_content_reports_target", "content_reports", ["target_type", "target_id"])

def downgrade() -> None:
    op.drop_index("ix_content_reports_target", table_name="content_reports")
    op.drop_index("ix_content_reports_status_created", table_name="content_reports")
    op.drop_index("ix_content_reports_reviewer_id", table_name="content_reports")
    op.drop_index("ix_content_reports_reporter_id", table_name="content_reports")
    op.drop_table("content_reports")

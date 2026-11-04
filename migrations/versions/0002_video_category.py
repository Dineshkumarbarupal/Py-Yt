"""Add catalog category metadata to videos."""
from alembic import op
import sqlalchemy as sa

revision = "0002_video_category"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("videos", sa.Column("category", sa.String(length=40), nullable=False, server_default="General"))
    op.alter_column("videos", "category", server_default=None)

def downgrade() -> None:
    op.drop_column("videos", "category")

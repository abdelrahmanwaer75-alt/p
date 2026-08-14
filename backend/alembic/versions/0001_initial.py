"""initial shared database schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.String(36), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("password_hash", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("email"))
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_table("download_tasks", sa.Column("id", sa.String(36), primary_key=True), sa.Column("owner_id", sa.String(36)), sa.Column("source_url", sa.Text(), nullable=False), sa.Column("format_id", sa.String(80), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("progress_percent", sa.Float()), sa.Column("progress_known", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("error_message", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_download_tasks_owner_id", "download_tasks", ["owner_id"], unique=False)
    op.create_table("library_items", sa.Column("id", sa.String(36), primary_key=True), sa.Column("owner_id", sa.String(36), nullable=False), sa.Column("title", sa.String(200), nullable=False), sa.Column("source_url", sa.Text(), nullable=False), sa.Column("media_path", sa.Text()), sa.Column("media_type", sa.String(40), nullable=False), sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("viewed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_library_items_owner_id", "library_items", ["owner_id"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_library_items_owner_id", table_name="library_items")
    op.drop_table("library_items")
    op.drop_index("ix_download_tasks_owner_id", table_name="download_tasks")
    op.drop_table("download_tasks")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

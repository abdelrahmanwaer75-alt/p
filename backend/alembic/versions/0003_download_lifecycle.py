"""add download lifecycle fields

Revision ID: 0003_download_lifecycle
Revises: 0002_auth_and_relational_library
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_download_lifecycle"
down_revision = "0002_auth_and_relational_library"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("download_tasks", sa.Column("user_id", sa.String(36), nullable=True))
    op.execute("UPDATE download_tasks SET user_id = owner_id WHERE user_id IS NULL")
    with op.batch_alter_table("download_tasks") as batch:
        batch.alter_column("user_id", nullable=False)
        batch.create_foreign_key("fk_download_tasks_user_id_users", "users", ["user_id"], ["id"], ondelete="CASCADE")
        batch.create_index("ix_download_tasks_user_id", ["user_id"])
        batch.create_index("ix_download_tasks_user_status", ["user_id", "status"])

    op.add_column("download_tasks", sa.Column("platform", sa.String(30), nullable=True))
    op.add_column("download_tasks", sa.Column("title", sa.String(500), nullable=True))
    op.add_column("download_tasks", sa.Column("format_type", sa.String(20), nullable=True))
    op.add_column("download_tasks", sa.Column("extension", sa.String(20), nullable=True))
    op.add_column("download_tasks", sa.Column("mime_type", sa.String(120), nullable=True))
    op.add_column("download_tasks", sa.Column("quality", sa.String(80), nullable=True))
    op.add_column("download_tasks", sa.Column("bytes_downloaded", sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column("download_tasks", sa.Column("total_bytes", sa.BigInteger(), nullable=True))
    op.add_column("download_tasks", sa.Column("speed", sa.Float(), nullable=True))
    op.add_column("download_tasks", sa.Column("eta", sa.Integer(), nullable=True))
    op.add_column("download_tasks", sa.Column("output_path", sa.Text(), nullable=True))
    op.add_column("download_tasks", sa.Column("output_filename", sa.String(500), nullable=True))
    op.add_column("download_tasks", sa.Column("error_code", sa.String(80), nullable=True))
    op.add_column("download_tasks", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("download_tasks", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("download_tasks", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("download_tasks", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("download_tasks", sa.Column("idempotency_key", sa.String(255), nullable=True))
    op.execute("UPDATE download_tasks SET platform = 'generic' WHERE platform IS NULL")
    op.execute("UPDATE download_tasks SET status = 'downloading' WHERE status = 'running'")
    with op.batch_alter_table("download_tasks") as batch:
        batch.alter_column("platform", nullable=False)
        batch.create_index("uq_download_tasks_user_idempotency", ["user_id", "idempotency_key"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("download_tasks") as batch:
        batch.drop_index("uq_download_tasks_user_idempotency")
        batch.drop_index("ix_download_tasks_user_status")
        batch.drop_index("ix_download_tasks_user_id")
        batch.drop_constraint("fk_download_tasks_user_id_users", type_="foreignkey")
        batch.drop_column("user_id")
        batch.drop_column("idempotency_key")
        batch.drop_column("retry_count")
        batch.drop_column("cancelled_at")
        batch.drop_column("completed_at")
        batch.drop_column("started_at")
        batch.drop_column("error_code")
        batch.drop_column("output_filename")
        batch.drop_column("output_path")
        batch.drop_column("eta")
        batch.drop_column("speed")
        batch.drop_column("total_bytes")
        batch.drop_column("bytes_downloaded")
        batch.drop_column("quality")
        batch.drop_column("mime_type")
        batch.drop_column("extension")
        batch.drop_column("format_type")
        batch.drop_column("title")
        batch.drop_column("platform")

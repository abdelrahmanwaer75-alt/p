"""add library file metadata

Revision ID: 0004_library_file_metadata
Revises: 0003_download_lifecycle
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_library_file_metadata"
down_revision = "0003_download_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("library_items", sa.Column("filename", sa.String(500), nullable=True))
    op.add_column("library_items", sa.Column("mime_type", sa.String(120), nullable=True))
    op.add_column("library_items", sa.Column("file_size", sa.BigInteger(), nullable=True))
    op.add_column("library_items", sa.Column("duration", sa.Integer(), nullable=True))
    op.add_column("library_items", sa.Column("thumbnail", sa.Text(), nullable=True))
    op.add_column("library_items", sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("library_items") as batch:
        batch.drop_column("downloaded_at")
        batch.drop_column("thumbnail")
        batch.drop_column("duration")
        batch.drop_column("file_size")
        batch.drop_column("mime_type")
        batch.drop_column("filename")

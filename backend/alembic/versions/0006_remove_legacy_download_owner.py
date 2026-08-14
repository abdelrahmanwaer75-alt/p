"""remove legacy download owner column

Revision ID: 0006_remove_legacy_download_owner
Revises: 0005_playlists
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_remove_legacy_download_owner"
down_revision = "0005_playlists"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("download_tasks")}
    indexes = {index["name"] for index in inspector.get_indexes("download_tasks")}
    foreign_keys = {foreign_key.get("name") for foreign_key in inspector.get_foreign_keys("download_tasks")}
    if "ix_download_tasks_owner_id" in indexes:
        op.drop_index("ix_download_tasks_owner_id", table_name="download_tasks")
    if "ix_download_tasks_owner_status" in indexes:
        op.drop_index("ix_download_tasks_owner_status", table_name="download_tasks")
    if "owner_id" in columns:
        with op.batch_alter_table("download_tasks") as batch:
            if "fk_download_tasks_owner_id_users" in foreign_keys:
                batch.drop_constraint("fk_download_tasks_owner_id_users", type_="foreignkey")
            batch.drop_column("owner_id")


def downgrade() -> None:
    op.add_column("download_tasks", sa.Column("owner_id", sa.String(36), nullable=True))
    op.execute("UPDATE download_tasks SET owner_id = user_id WHERE owner_id IS NULL")

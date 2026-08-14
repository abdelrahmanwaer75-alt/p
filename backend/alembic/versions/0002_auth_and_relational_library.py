"""add auth state and relational library records

Revision ID: 0002_auth_and_relational_library
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_auth_and_relational_library"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("verification_token_hash", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("verification_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("password_reset_token_hash", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    op.execute("UPDATE users SET updated_at = created_at WHERE updated_at IS NULL")
    with op.batch_alter_table("users") as batch:
        batch.alter_column("updated_at", nullable=False)
        batch.create_unique_constraint("uq_users_verification_token_hash", ["verification_token_hash"])
        batch.create_unique_constraint("uq_users_password_reset_token_hash", ["password_reset_token_hash"])

    op.add_column("download_tasks", sa.Column("_owner_id_migration_check", sa.String(36), nullable=True))
    op.execute("UPDATE download_tasks SET _owner_id_migration_check = owner_id")
    op.drop_column("download_tasks", "_owner_id_migration_check")
    with op.batch_alter_table("download_tasks") as batch:
        batch.alter_column("owner_id", nullable=False)
        batch.create_foreign_key("fk_download_tasks_owner_id_users", "users", ["owner_id"], ["id"], ondelete="CASCADE")
        batch.create_index("ix_download_tasks_owner_status", ["owner_id", "status"])

    op.add_column("library_items", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE library_items SET updated_at = created_at WHERE updated_at IS NULL")
    with op.batch_alter_table("library_items") as batch:
        batch.alter_column("updated_at", nullable=False)
        batch.create_foreign_key("fk_library_items_owner_id_users", "users", ["owner_id"], ["id"], ondelete="CASCADE")

    op.create_table(
        "favorites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("library_item_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["library_item_id"], ["library_items.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "library_item_id", name="uq_favorites_user_item"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"], unique=False)
    op.create_index("ix_favorites_library_item_id", "favorites", ["library_item_id"], unique=False)

    op.create_table(
        "history_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("library_item_id", sa.String(36), nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["library_item_id"], ["library_items.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "library_item_id", name="uq_history_user_item"),
    )
    op.create_index("ix_history_items_user_id", "history_items", ["user_id"], unique=False)
    op.create_index("ix_history_items_library_item_id", "history_items", ["library_item_id"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=False)
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_history_items_library_item_id", table_name="history_items")
    op.drop_index("ix_history_items_user_id", table_name="history_items")
    op.drop_table("history_items")
    op.drop_index("ix_favorites_library_item_id", table_name="favorites")
    op.drop_index("ix_favorites_user_id", table_name="favorites")
    op.drop_table("favorites")
    with op.batch_alter_table("library_items") as batch:
        batch.drop_constraint("fk_library_items_owner_id_users", type_="foreignkey")
        batch.drop_column("updated_at")
    with op.batch_alter_table("download_tasks") as batch:
        batch.drop_index("ix_download_tasks_owner_status")
        batch.drop_constraint("fk_download_tasks_owner_id_users", type_="foreignkey")
        batch.alter_column("owner_id", nullable=True)
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("uq_users_password_reset_token_hash", type_="unique")
        batch.drop_constraint("uq_users_verification_token_hash", type_="unique")
        batch.drop_column("token_version")
        batch.drop_column("password_reset_expires_at")
        batch.drop_column("password_reset_token_hash")
        batch.drop_column("verification_expires_at")
        batch.drop_column("verification_token_hash")
        batch.drop_column("is_verified")
        batch.drop_column("is_active")
        batch.drop_column("updated_at")

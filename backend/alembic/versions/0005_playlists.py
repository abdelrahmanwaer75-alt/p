"""add playlists and playlist items

Revision ID: 0005_playlists
Revises: 0004_library_file_metadata
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_playlists"
down_revision = "0004_library_file_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "playlists",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_playlists_user_id", "playlists", ["user_id"])
    op.create_index("ix_playlists_user_name", "playlists", ["user_id", "name"])
    op.create_table(
        "playlist_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("playlist_id", sa.String(length=36), nullable=False),
        sa.Column("library_item_id", sa.String(length=36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["library_item_id"], ["library_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["playlist_id"], ["playlists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("playlist_id", "library_item_id", name="uq_playlist_library_item"),
    )
    op.create_index("ix_playlist_items_playlist_id", "playlist_items", ["playlist_id"])
    op.create_index("ix_playlist_items_library_item_id", "playlist_items", ["library_item_id"])
    op.create_index("ix_playlist_items_order", "playlist_items", ["playlist_id", "position"])


def downgrade() -> None:
    op.drop_index("ix_playlist_items_order", table_name="playlist_items")
    op.drop_index("ix_playlist_items_library_item_id", table_name="playlist_items")
    op.drop_index("ix_playlist_items_playlist_id", table_name="playlist_items")
    op.drop_table("playlist_items")
    op.drop_index("ix_playlists_user_name", table_name="playlists")
    op.drop_index("ix_playlists_user_id", table_name="playlists")
    op.drop_table("playlists")

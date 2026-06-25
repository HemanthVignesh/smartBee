"""add users table and user_id to emails

Revision ID: 0002_add_auth
Revises: 0001_initial
Create Date: 2026-06-25
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_auth"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Create users table ────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("google_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("picture", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="1"),
        sa.Column("is_verified", sa.Boolean(), nullable=True, server_default="1"),
        sa.Column("gmail_token_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("google_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── 2. Add user_id FK to emails ───────────────────────────────────────────
    # SQLite doesn't support ALTER TABLE ADD CONSTRAINT, so we use batch mode.
    with op.batch_alter_table("emails") as batch_op:
        batch_op.add_column(
            sa.Column(
                "user_id",
                sa.String(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=True,   # nullable so existing rows aren't broken
            )
        )
        batch_op.create_index("ix_emails_user_id", ["user_id"])


def downgrade() -> None:
    with op.batch_alter_table("emails") as batch_op:
        batch_op.drop_index("ix_emails_user_id")
        batch_op.drop_column("user_id")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_table("users")

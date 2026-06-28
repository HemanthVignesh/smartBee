"""
Add users table and user_id FK to email_logs.
Revision: 0002
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_users"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id",            sa.Integer(),      primary_key=True, autoincrement=True),
        sa.Column("email",         sa.String(320),    nullable=False),
        sa.Column("display_name",  sa.String(128),    nullable=True),
        sa.Column("password_hash", sa.String(256),    nullable=False),
        sa.Column("is_active",     sa.Boolean(),      nullable=False, server_default="1"),
        sa.Column("is_verified",   sa.Boolean(),      nullable=False, server_default="0"),
        sa.Column("created_at",    sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Add nullable FK so existing email_log rows are not broken
    op.add_column(
        "email_logs",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
    )
    op.create_index("ix_email_logs_user_id", "email_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_email_logs_user_id", table_name="email_logs")
    op.drop_column("email_logs", "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

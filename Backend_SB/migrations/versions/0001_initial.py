"""
Initial migration — create email_logs and secure_settings tables.
Generated: 2025-06-25
Revision: 0001
"""

from alembic import op
import sqlalchemy as sa

# Alembic identifiers
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_logs",
        sa.Column("id",         sa.Integer(),     primary_key=True, autoincrement=True),
        sa.Column("sender",     sa.String(320),   nullable=False),
        sa.Column("subject",    sa.Text(),         nullable=False),
        sa.Column("intent",     sa.String(64),    nullable=False),
        sa.Column("confidence", sa.Float(),        nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_email_logs_sender",     "email_logs", ["sender"])
    op.create_index("ix_email_logs_intent",     "email_logs", ["intent"])
    op.create_index("ix_email_logs_created_at", "email_logs", ["created_at"])

    op.create_table(
        "secure_settings",
        sa.Column("key",   sa.String(128), primary_key=True),
        sa.Column("value", sa.Text(),      nullable=False),
    )


def downgrade() -> None:
    op.drop_table("secure_settings")
    op.drop_index("ix_email_logs_created_at", table_name="email_logs")
    op.drop_index("ix_email_logs_intent",     table_name="email_logs")
    op.drop_index("ix_email_logs_sender",     table_name="email_logs")
    op.drop_table("email_logs")

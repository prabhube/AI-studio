"""Extend users table with auth fields (role, OAuth, email_verified, last_login_at)

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-01 00:00:00.000000

Changes:
  - Make hashed_password nullable (OAuth users have no local password)
  - Add role (VARCHAR 20, default 'user')
  - Add avatar_url (VARCHAR 2048, nullable)
  - Add email_verified (BOOLEAN, default false)
  - Add last_login_at (TIMESTAMP WITH TIME ZONE, nullable)
  - Add oauth_provider (VARCHAR 50, nullable)
  - Add oauth_provider_id (VARCHAR 255, nullable)
  - Add is_admin computed index (role IN ('admin','superuser'))
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make hashed_password nullable — existing rows keep their value
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(255),
        nullable=True,
    )

    # Role column
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            server_default="user",
        ),
    )
    op.create_index("ix_users_role", "users", ["role"])

    # Avatar URL
    op.add_column(
        "users",
        sa.Column("avatar_url", sa.String(2048), nullable=True),
    )

    # Email verification
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )

    # Last login timestamp
    op.add_column(
        "users",
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # OAuth fields
    op.add_column(
        "users",
        sa.Column("oauth_provider", sa.String(50), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("oauth_provider_id", sa.String(255), nullable=True),
    )

    op.create_index("ix_users_oauth_provider", "users", ["oauth_provider"])
    op.create_index("ix_users_oauth_provider_id", "users", ["oauth_provider_id"])

    # Composite index for fast OAuth lookup
    op.create_index(
        "ix_users_oauth_provider_and_id",
        "users",
        ["oauth_provider", "oauth_provider_id"],
    )

    # Backfill is_superuser from role (for any future superusers created before this migration)
    op.execute(
        "UPDATE users SET role = 'superuser', is_superuser = true "
        "WHERE is_superuser = true AND role = 'user'"
    )


def downgrade() -> None:
    op.drop_index("ix_users_oauth_provider_and_id", table_name="users")
    op.drop_index("ix_users_oauth_provider_id", table_name="users")
    op.drop_index("ix_users_oauth_provider", table_name="users")
    op.drop_index("ix_users_role", table_name="users")

    op.drop_column("users", "oauth_provider_id")
    op.drop_column("users", "oauth_provider")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "role")

    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(255),
        nullable=False,
    )

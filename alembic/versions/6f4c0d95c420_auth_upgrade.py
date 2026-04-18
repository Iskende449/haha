"""auth and user profile upgrade

Revision ID: 6f4c0d95c420
Revises: cfb17d6761c4
Create Date: 2026-04-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6f4c0d95c420'
down_revision: Union[str, None] = 'cfb17d6761c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('hashed_password', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('experience_points', sa.Integer(), server_default='0', nullable=False))

    op.execute("UPDATE users SET email = username || '@legacy.local' WHERE email IS NULL")
    op.execute("UPDATE users SET hashed_password = '' WHERE hashed_password IS NULL")
    op.execute("UPDATE users SET full_name = username WHERE full_name IS NULL")

    op.alter_column('users', 'email', nullable=False)
    op.alter_column('users', 'hashed_password', nullable=False)
    op.alter_column('users', 'full_name', nullable=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.drop_index('ix_users_username', table_name='users')
    op.drop_column('users', 'username')

    op.add_column('user_progress', sa.Column('legend_quest', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('user_progress', 'legend_quest')

    op.add_column('users', sa.Column('username', sa.String(length=64), nullable=True))
    op.execute("UPDATE users SET username = split_part(email, '@', 1) WHERE username IS NULL")
    op.alter_column('users', 'username', nullable=False)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    op.drop_index('ix_users_email', table_name='users')
    op.drop_column('users', 'experience_points')
    op.drop_column('users', 'full_name')
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'email')

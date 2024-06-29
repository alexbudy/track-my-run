"""add email

Revision ID: 3d10732bc6e4
Revises: 14586d42fcd4
Create Date: 2024-06-24 06:13:52.379925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d10732bc6e4'
down_revision: Union[str, None] = '14586d42fcd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('cooper_points', 'distance_floor',
               existing_type=sa.NUMERIC(precision=5, scale=1),
               type_=sa.Numeric(precision=6, scale=2),
               existing_nullable=False)
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'email_verified_at')
    op.alter_column('cooper_points', 'distance_floor',
               existing_type=sa.Numeric(precision=6, scale=2),
               type_=sa.NUMERIC(precision=5, scale=1),
               existing_nullable=False)
    # ### end Alembic commands ###
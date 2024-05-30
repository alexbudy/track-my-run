"""activity type added to runs table

Revision ID: 767dd5a5f8ca
Revises: 89eae62594f6
Create Date: 2024-05-30 12:38:25.423601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '767dd5a5f8ca'
down_revision: Union[str, None] = '89eae62594f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('runs', sa.Column('activity_type', sa.String(), server_default='run', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('runs', 'activity_type')
    # ### end Alembic commands ###
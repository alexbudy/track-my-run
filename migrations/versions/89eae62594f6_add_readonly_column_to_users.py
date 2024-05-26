"""add readonly column to users

Revision ID: 89eae62594f6
Revises: 5b227b322350
Create Date: 2024-05-26 11:54:00.737953

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "89eae62594f6"
down_revision: Union[str, None] = "5b227b322350"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users",
        sa.Column("is_readonly", sa.Integer(), nullable=False, server_default="0"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "is_readonly")
    # ### end Alembic commands ###

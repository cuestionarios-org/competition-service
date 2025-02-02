"""Make dates nullable

Revision ID: 5f091fb12172
Revises: c97c3ae106d1
Create Date: 2025-02-02 16:32:39.906203

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5f091fb12172'
down_revision = 'c97c3ae106d1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('competitions', schema=None) as batch_op:
        batch_op.alter_column('start_date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True)
        batch_op.alter_column('end_date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('competitions', schema=None) as batch_op:
        batch_op.alter_column('end_date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False)
        batch_op.alter_column('start_date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False)

    # ### end Alembic commands ###

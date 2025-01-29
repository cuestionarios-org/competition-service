"""inicial

Revision ID: ee4e43bef5a0
Revises: 
Create Date: 2025-01-29 09:02:07.845968

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee4e43bef5a0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('competitions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('state', sa.String(length=50), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('modified_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=False),
    sa.Column('participant_limit', sa.Integer(), nullable=False),
    sa.Column('currency_cost', sa.Integer(), nullable=False),
    sa.Column('ticket_cost', sa.Integer(), nullable=False),
    sa.Column('credit_cost', sa.Integer(), nullable=False),
    sa.CheckConstraint('credit_cost >= 0', name='check_credit_cost_positive'),
    sa.CheckConstraint('currency_cost >= 0', name='check_currency_cost_positive'),
    sa.CheckConstraint('participant_limit >= 0', name='check_participant_limit_positive'),
    sa.CheckConstraint('start_date < end_date', name='check_valid_dates'),
    sa.CheckConstraint('ticket_cost >= 0', name='check_ticket_cost_positive'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('competitions', schema=None) as batch_op:
        batch_op.create_index('idx_state_end_date', ['state', 'end_date'], unique=False)

    op.create_table('competition_participants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('competition_id', sa.Integer(), nullable=False),
    sa.Column('participant_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['competition_id'], ['competitions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('competition_id', 'participant_id', name='uq_competition_participant')
    )
    op.create_table('competition_quizzes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('competition_id', sa.Integer(), nullable=False),
    sa.Column('quiz_id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('end_time', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['competition_id'], ['competitions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('competition_id', 'quiz_id', name='uq_competition_quiz')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('competition_quizzes')
    op.drop_table('competition_participants')
    with op.batch_alter_table('competitions', schema=None) as batch_op:
        batch_op.drop_index('idx_state_end_date')

    op.drop_table('competitions')
    # ### end Alembic commands ###

"""Add score_competion in comp_quiz_participants and status y competition_quiz

Revision ID: 7c23977f9265
Revises: 40c36011e5fd
Create Date: 2025-02-05 08:38:31.558331

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c23977f9265'
down_revision = '40c36011e5fd'
branch_labels = None
depends_on = None


def upgrade():
    # 0️⃣ Crear el tipo ENUM antes de usarlo en la columna
    op.execute("CREATE TYPE competitionquizstatus AS ENUM ('ACTIVO', 'COMPUTABLE', 'NO_COMPUTABLE')")

    # 1️⃣ Agregar la nueva columna como nullable=True temporalmente
    with op.batch_alter_table('competition_quizzes', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'status',
            sa.Enum('ACTIVO', 'COMPUTABLE', 'NO_COMPUTABLE', name='competitionquizstatus'),
            nullable=True,  # ✅ Agregar como NULL inicialmente
            comment='Estado del cuestionario dentro de la competencia'
        ))

    # 2️⃣ Asignar el estado "ACTIVO" a todas las filas existentes
    op.execute("UPDATE competition_quizzes SET status = 'ACTIVO'")

    # 3️⃣ Cambiar la columna a NOT NULL después de asignar valores
    with op.batch_alter_table('competition_quizzes', schema=None) as batch_op:
        batch_op.alter_column('status', nullable=False)

    # 4️⃣ Agregar la columna 'score_competition' sin problema
    with op.batch_alter_table('competition_quizzes_participants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('score_competition', sa.Integer(), nullable=True))

def downgrade():
    # Eliminar la columna 'score_competition'
    with op.batch_alter_table('competition_quizzes_participants', schema=None) as batch_op:
        batch_op.drop_column('score_competition')

    # Eliminar la columna 'status'
    with op.batch_alter_table('competition_quizzes', schema=None) as batch_op:
        batch_op.drop_column('status')

    # Eliminar el tipo ENUM 'competitionquizstatus'
    op.execute("DROP TYPE competitionquizstatus")

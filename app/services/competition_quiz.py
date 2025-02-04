from sqlalchemy import select, and_, func, update, bindparam
from sqlalchemy.orm import load_only
from extensions import db
from app.models import CompetitionQuiz, CompetitionQuizParticipants, CompetitionParticipant


class CompetitionQuizService:
    @staticmethod
    def process_quiz_results(competition_quiz):
        """
        Procesa un quiz con control de concurrencia y transacciones atómicas.
        Devuelve True si el procesamiento fue exitoso.
        """
        try:
            # Bloquear y recargar el registro para evitar race conditions
            locked_quiz = db.session.execute(
                select(CompetitionQuiz)
                .where(
                    CompetitionQuiz.id == competition_quiz.id,
                    CompetitionQuiz.processed == False  # noqa: E712
                )
                .execution_options(populate_existing=True)
                .with_for_update()
            ).scalar_one_or_none()

            if not locked_quiz:
                print(f"🟡 Quiz {competition_quiz.id} ya procesado o no existe")
                return False

            print(f"🟢 Iniciando procesamiento quiz {locked_quiz.id}")

            with db.session.begin_nested():
                CompetitionQuizService._calculate_results(locked_quiz)
                locked_quiz.processed = True

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"🔴 Error crítico procesando quiz {competition_quiz.id}: {str(e)}")
            return False

    @staticmethod
    def _calculate_results(quiz):
        """Lógica central de cálculo de resultados con batch updates"""
        # 1. Obtener participaciones válidas ordenadas
        participations = db.session.scalars(
            select(CompetitionQuizParticipants)
            .where(
                CompetitionQuizParticipants.competition_quiz_id == quiz.id,
                CompetitionQuizParticipants.end_time.isnot(None)
            )
            .order_by(CompetitionQuizParticipants.score.desc())
        ).all()

        if not participations:
            print(f"⚪ Quiz {quiz.id} sin participaciones válidas")
            return

        # 2. Obtener IDs de participantes para batch query
        participant_ids = [p.participant_id for p in participations]
        
        # 3. Actualización masiva de scores usando SQLAlchemy Core para performance
        puntos_por_puesto = [10, 8, 6, 5, 4, 3, 2, 1]
        update_values = []
        
        for idx, part in enumerate(participations):
            puntos = puntos_por_puesto[idx] if idx < len(puntos_por_puesto) else 1
            update_values.append({
                "participant_id": part.participant_id,
                "competition_id": quiz.competition_id,
                "puntos": puntos
            })

        # 4. Update using bulk update
        if update_values:
            # 🔥 Corrección clave: Usar SQLAlchemy Core con tabla explícita
            table = CompetitionParticipant.__table__
            
            stmt = (
                update(table)
                .where(
                    and_(
                        table.c.participant_id == bindparam('p_participant_id'),
                        table.c.competition_id == bindparam('p_competition_id')
                    )
                )
                .values(score=table.c.score + bindparam('p_puntos'))
            )

            # Parámetros renombrados para evitar conflicto
            params = [
                {
                    "p_participant_id": item["participant_id"],
                    "p_competition_id": item["competition_id"],
                    "p_puntos": item["puntos"]
                }
                for item in update_values
            ]

            db.session.execute(
                stmt,
                params,
                execution_options={"synchronize_session": False}
            )
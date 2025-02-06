from sqlalchemy import select, and_, update, bindparam
from sqlalchemy.orm import load_only
from extensions import db
from app.models import CompetitionQuiz, CompetitionQuizParticipants, CompetitionParticipant

from datetime import datetime, timezone

from app.utils.lib.constants import CompetitionQuizStatus

class CompetitionQuizService:
    @staticmethod
    def process_quiz_results(competition_quiz):
        """
        Procesa un quiz con control de concurrencia y transacciones atómicas.
        Devuelve True si el procesamiento fue exitoso.
        """
        try:
            # 🔹 Bloquear y recargar el registro para evitar race conditions
            locked_quiz = db.session.execute(
                select(CompetitionQuiz)
                .where(
                    CompetitionQuiz.id == competition_quiz.id,
                    CompetitionQuiz.status == CompetitionQuizStatus.ACTIVO  
                )
                .execution_options(populate_existing=True)
                .with_for_update()
            ).scalar_one_or_none()

            if not locked_quiz:
                print(f"🟡 Quiz {competition_quiz.id} ya procesado o no existe")
                return False

            print(f"🟢 Iniciando procesamiento quiz {locked_quiz.id}")

            # 🔹 Aquí ya hay una transacción implícita
            CompetitionQuizService._calculate_results(locked_quiz)
            locked_quiz.set_status(CompetitionQuizStatus.COMPUTABLE)
            db.session.add(locked_quiz)  # Asegurar que el cambio se registre en la sesión

            db.session.commit()  # 🔥 Este commit es suficiente para todos los cambios

            return True  

        except Exception as e:
            db.session.rollback()  # Asegurar rollback en cualquier error
            print(f"🔴 Error crítico procesando quiz {competition_quiz.id}: {str(e)}")
            return False

    @staticmethod
    def _calculate_results(quiz):
        """Lógica actualizada para escribir en score_competition"""
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

        # 2. Asignar puntos según posición
        puntos_por_puesto = [10, 8, 6, 5, 4, 3, 2, 1]

        # 3. Actualizar score_competition directamente en la misma sesión
        for idx, participation in enumerate(participations):
            participation.score_competition = puntos_por_puesto[idx] if idx < len(puntos_por_puesto) else 1

        # 🔹 Bulk update sin commit aquí
        db.session.bulk_update_mappings(
            CompetitionQuizParticipants,
            [
                {
                    'id': p.id,
                    'score_competition': p.score_competition,
                    'updated_at': datetime.now(timezone.utc)
                }
                for p in participations
            ]
        )

        # 🔥 No hacer `db.session.commit()` aquí, solo en `process_quiz_results()`

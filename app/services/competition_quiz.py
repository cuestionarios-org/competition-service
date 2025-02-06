from sqlalchemy import select, and_, update, bindparam
from sqlalchemy.orm import load_only
from extensions import db
from app.models import CompetitionQuiz, CompetitionQuizParticipants
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

            # 🔹 Calcular resultados del quiz
            CompetitionQuizService._calculate_results(locked_quiz)

            # 🔹 Marcar como COMPUTABLE
            locked_quiz.set_status(CompetitionQuizStatus.COMPUTABLE)
            db.session.add(locked_quiz)

            # 🔹 Verificar límite de quizzes COMPUTABLES (máximo 5)
            CompetitionQuizService._enforce_computable_limit(locked_quiz.competition_id)

            db.session.commit()  # 🔥 Un solo commit para todo

            return True  

        except Exception as e:
            db.session.rollback()  # Asegurar rollback en cualquier error
            print(f"🔴 Error crítico procesando quiz {competition_quiz.id}: {str(e)}")
            return False

    @staticmethod
    def _calculate_results(quiz):
        """Lógica para escribir en score_competition"""
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

        puntos_por_puesto = [10, 8, 6, 5, 4, 3, 2, 1]
        for idx, participation in enumerate(participations):
            participation.score_competition = puntos_por_puesto[idx] if idx < len(puntos_por_puesto) else 1

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

    @staticmethod
    def _enforce_computable_limit(competition_id):
        """Asegura que solo haya 5 quizzes COMPUTABLE en una competencia"""
        computable_quizzes = db.session.scalars(
            select(CompetitionQuiz)
            .where(
                CompetitionQuiz.competition_id == competition_id,
                CompetitionQuiz.status == CompetitionQuizStatus.COMPUTABLE
            )
            .order_by(CompetitionQuiz.end_time.asc())  # 🔹 Ordenar por fecha más antigua
        ).all()

        if len(computable_quizzes) > 3:
            quiz_to_downgrade = computable_quizzes[0]  # El más antiguo
            quiz_to_downgrade.set_status(CompetitionQuizStatus.NO_COMPUTABLE)
            db.session.add(quiz_to_downgrade)
            print(f"🔻 Quiz {quiz_to_downgrade.id} cambiado a NO_COMPUTABLE")

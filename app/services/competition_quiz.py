from sqlalchemy import select, and_
from extensions import db

from app.models import CompetitionQuizParticipants, CompetitionParticipant


class CompetitionQuizService:
    @staticmethod
    def process_quiz_results(competition_quiz):
        """Procesa los resultados de un quiz en la competencia."""
        try:
            print("Procesando quiz", competition_quiz)
            print("Competencia", competition_quiz.competition_id, "start_time", competition_quiz.start_time, "end_time", competition_quiz.end_time)

            # Calcular y asignar resultados
            CompetitionQuizService._calculate_results(competition_quiz)

            # Marcar el quiz como procesado
            competition_quiz.processed = True
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"Error procesando el quiz {competition_quiz}: {e}")

    @staticmethod
    def _calculate_results(quiz):
        """Realiza el cálculo de resultados del quiz y asigna puntajes acumulativos."""
        participations = db.session.execute(
            select(CompetitionQuizParticipants)
            .where(and_(
                CompetitionQuizParticipants.competition_quiz_id == quiz.id,
                CompetitionQuizParticipants.end_time.isnot(None)
            ))
        ).scalars().all()

        if not participations:
            return

        # 🔹 Ordenar participantes por score (descendente)
        participations.sort(key=lambda x: x.score, reverse=True)

        # 🔹 Definir los puntajes a asignar
        puntos_por_puesto = [10, 8, 6, 5, 4, 3, 2, 1]

        # 🔹 Asignar puntos y actualizar `CompetitionParticipant`
        for idx, participation in enumerate(participations):
            puntos = puntos_por_puesto[idx] if idx < len(puntos_por_puesto) else 0
            
            # Buscar el participante en CompetitionParticipant
            participant = db.session.execute(
                select(CompetitionParticipant).where(and_(
                    CompetitionParticipant.competition_id == quiz.competition_id,
                    CompetitionParticipant.participant_id == participation.participant_id
                ))
            ).scalar_one_or_none()

            if participant:
                participant.score += puntos  # 🔹 Sumar puntos al score acumulado

        db.session.commit()

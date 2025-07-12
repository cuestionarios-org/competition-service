from sqlalchemy import select, func
from sqlalchemy.orm import load_only
from extensions import db
from app.models import CompetitionQuiz, CompetitionQuizParticipants, CompetitionParticipant
from datetime import datetime, timezone
from app.utils.lib.constants import CompetitionQuizStatus
from werkzeug.exceptions import NotFound, BadRequest

class CompetitionQuizService:
    @staticmethod
    def process_quiz_results(competition_quiz):
        """
        Procesa un quiz con control de concurrencia y transacciones atómicas.
        Devuelve True si el procesamiento fue exitoso.
        """
        try:
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

            CompetitionQuizService._calculate_results(locked_quiz)
            locked_quiz.set_status(CompetitionQuizStatus.COMPUTABLE)
            db.session.add(locked_quiz)

            # 🔹 Controlar que no haya más de X quizzes COMPUTABLES
            CompetitionQuizService._enforce_computable_limit(locked_quiz.competition_id)

            # 🔹 Recalcular puntajes de la competencia
            CompetitionQuizService._update_competition_scores(locked_quiz.competition_id)

            db.session.commit()  # 🔥 Un solo commit para todo

            return True  

        except Exception as e:
            db.session.rollback()  
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
        """Asegura que solo haya X quizzes COMPUTABLE en una competencia"""
        computable_quizzes = db.session.scalars(
            select(CompetitionQuiz)
            .where(
                CompetitionQuiz.competition_id == competition_id,
                CompetitionQuiz.status == CompetitionQuizStatus.COMPUTABLE
            )
            .order_by(CompetitionQuiz.end_time.asc())  
        ).all()

        if len(computable_quizzes) > 5:  # Ajusta el límite aquí si cambia
            quiz_to_downgrade = computable_quizzes[0]  # El más antiguo
            quiz_to_downgrade.set_status(CompetitionQuizStatus.NO_COMPUTABLE)
            db.session.add(quiz_to_downgrade)
            print(f"🔻 Quiz {quiz_to_downgrade.id} cambiado a NO_COMPUTABLE")

    @staticmethod
    def _update_competition_scores(competition_id):
        """Recalcula los puntajes de todos los participantes de la competencia"""
        print(f"🔄 Recalculando puntajes para competencia {competition_id}")

        # 🔹 Obtener la suma de score_competition por participante en quizzes COMPUTABLES
        participant_scores = db.session.execute(
            select(
                CompetitionQuizParticipants.participant_id,
                func.sum(CompetitionQuizParticipants.score_competition).label("total_score")
            )
            .join(CompetitionQuiz, CompetitionQuiz.id == CompetitionQuizParticipants.competition_quiz_id)
            .where(
                CompetitionQuiz.competition_id == competition_id,
                CompetitionQuiz.status == CompetitionQuizStatus.COMPUTABLE
            )
            .group_by(CompetitionQuizParticipants.participant_id)
        ).all()

        if not participant_scores:
            print(f"⚪ No hay participantes con puntajes en competencia {competition_id}")
            return

        # 🔹 Obtener los IDs de CompetitionParticipant correspondientes
        participant_ids = [p[0] for p in participant_scores]

        participant_map = {
            p.participant_id: p.id for p in db.session.scalars(
                select(CompetitionParticipant)
                .where(
                    CompetitionParticipant.competition_id == competition_id,
                    CompetitionParticipant.participant_id.in_(participant_ids)
                )
                .options(load_only(CompetitionParticipant.id, CompetitionParticipant.participant_id))
            )
        }

        # 🔹 Preparar la actualización con los IDs correctos
        updates = [
            {
                "id": participant_map[participant_id],  # ✅ Ahora incluye el ID
                "score": total_score,
                "updated_at": datetime.now(timezone.utc)
            }
            for participant_id, total_score in participant_scores
            if participant_id in participant_map
        ]

        if updates:
            db.session.bulk_update_mappings(CompetitionParticipant, updates)
            print(f"✅ Puntajes recalculados para competencia {competition_id}")

    @staticmethod
    def update_competition_quiz(competition_quiz_id, data):
        quiz = CompetitionQuiz.query.get(competition_quiz_id)
        if not quiz:
            raise NotFound(f"CompetitionQuiz con ID {competition_quiz_id} no encontrado.")
        if 'start_time' in data:
            quiz.start_time = CompetitionQuizService._parse_datetime(data['start_time'])
        if 'end_time' in data:
            quiz.end_time = CompetitionQuizService._parse_datetime(data['end_time'])
        if 'time_limit' in data:
            quiz.time_limit = int(data['time_limit'])
        db.session.commit()
        return quiz

    @staticmethod
    def _parse_datetime(value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except Exception:
                raise BadRequest(f"Formato de fecha inválido: {value}. Usar ISO 8601.")
        if isinstance(value, datetime):
            return value
        raise BadRequest(f"Tipo de fecha inválido: {type(value)}")

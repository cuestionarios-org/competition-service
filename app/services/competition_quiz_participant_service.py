from app.models import CompetitionQuizParticipants, CompetitionQuiz, CompetitionParticipant,CompetitionQuizAnswer
from extensions import db
from werkzeug.exceptions import BadRequest, NotFound
import datetime as dt
from datetime  import timezone
from sqlalchemy.exc import SQLAlchemyError


class CompetitionQuizParticipantService:

    # 🧩 Validaciones privadas reutilizables
    @staticmethod
    def _get_quiz_or_404(competition_quiz_id):
        quiz = CompetitionQuiz.query.filter_by(id=competition_quiz_id).first()
        if not quiz:
            raise NotFound(f"Quiz with id {competition_quiz_id} not found.")
        return quiz

    @staticmethod
    def _check_participant_in_competition(competition_id, participant_id):
        participante = CompetitionParticipant.query.filter_by(
            competition_id=competition_id,
            participant_id=participant_id
        ).first()
        if not participante:
            raise NotFound(f"Participant {participant_id} is not registered in competition {competition_id}.")
        return participante

    @staticmethod
    def _check_time_availability(quiz):
        ahora = dt.datetime.now(timezone.utc)

        if not quiz.start_time:
            raise BadRequest(f"Quiz {quiz.id} does not have a start time configured.")

        if quiz.end_time:
            if ahora < quiz.start_time or ahora > quiz.end_time:
                raise BadRequest(f"Quiz {quiz.id} is not available at this time.")
        else:
            if ahora < quiz.start_time:
                raise BadRequest(f"Quiz {quiz.id} is not available yet.")

    @staticmethod
    def _check_participant_not_already_started(competition_quiz_id, participant_id):
        existing = CompetitionQuizParticipants.query.filter_by(
            competition_quiz_id=competition_quiz_id,
            participant_id=participant_id
        ).first()
        if existing:
            raise BadRequest(f"Participant {participant_id} already started quiz {competition_quiz_id}.")

    # 🧠 Método público para inscribir al participante en el quiz
    @staticmethod
    def add_participant_to_quiz(competition_quiz_id, participant_id):
        try:
            quiz = CompetitionQuizParticipantService._get_quiz_or_404(competition_quiz_id)
            CompetitionQuizParticipantService._check_participant_not_already_started(competition_quiz_id, participant_id)

            participant = CompetitionQuizParticipants(
                competition_quiz_id=competition_quiz_id,
                participant_id=participant_id,
                start_time=dt.datetime.now(timezone.utc)
            )
            db.session.add(participant)
            db.session.commit()
            return participant

        except (SQLAlchemyError, BadRequest, NotFound) as e:
            db.session.rollback()
            raise e  # Lo dejamos escalar para ser manejado por el handler global
        except Exception as e:
            db.session.rollback()
            raise BadRequest(f"An unexpected error occurred while adding participant: {str(e)}")

    # 🧠 Método público para iniciar el quiz
    @staticmethod
    def start_quiz(competition_quiz_id, participant_id):
        try:
            quiz = CompetitionQuizParticipantService._get_quiz_or_404(competition_quiz_id)
            competition_id = quiz.competition_id

            CompetitionQuizParticipantService._check_participant_in_competition(competition_id, participant_id)
            CompetitionQuizParticipantService._check_participant_not_already_started(competition_quiz_id, participant_id)
            CompetitionQuizParticipantService._check_time_availability(quiz)

            participante_alta_en_cuestionario = CompetitionQuizParticipants(
                competition_quiz_id=competition_quiz_id,
                participant_id=participant_id,
                start_time=db.func.now()
            )
            db.session.add(participante_alta_en_cuestionario)
            db.session.commit()

            return {
                "competition_id": competition_id,
                "participant_id": participant_id,
                "start_time": participante_alta_en_cuestionario.start_time.isoformat()
                    if participante_alta_en_cuestionario.start_time else None,
                "competition_quiz_participant_id": participante_alta_en_cuestionario.id,
                "quiz_id": quiz.quiz_id
            }

        except (SQLAlchemyError, BadRequest, NotFound) as e:
            db.session.rollback()
            raise e
        except Exception as e:
            db.session.rollback()
            raise BadRequest(f"An unexpected error occurred while starting quiz: {str(e)}")

    @staticmethod
    def finish_quiz(competition_quiz_id, participant_id, answers):
        """
        Registra el tiempo de finalización y guarda las respuestas validadas con su corrección.
        """
        time_finish = dt.datetime.now(timezone.utc)
        
        cuestionario_en_competencia = CompetitionQuiz.query.get(competition_quiz_id)
        if not cuestionario_en_competencia:
            raise NotFound(f"Competition quiz with ID {competition_quiz_id} not found.")
        
        competition_id = cuestionario_en_competencia.competition_id

        # Validar inscripción en competencia
        if not CompetitionParticipant.query.filter_by(
            competition_id=competition_id,
            participant_id=participant_id
        ).first():
            raise NotFound(f"Participant {participant_id} not registered in competition {competition_id}.")

        # Obtener participación en cuestionario
        participante_en_cuestionario = CompetitionQuizParticipants.query.filter_by(
            competition_quiz_id=competition_quiz_id,
            participant_id=participant_id
        ).first()

        if not participante_en_cuestionario:
            raise BadRequest(f"Participant {participant_id} hasn't started this quiz.")

        if participante_en_cuestionario.end_time:
            raise BadRequest("Quiz already completed.")

        # Validación de tiempo límite mejorada
        time_limit = cuestionario_en_competencia.time_limit
        if time_limit > 0:
            time_start = participante_en_cuestionario.start_time
            tiempo_transcurrido = (time_finish - time_start).total_seconds()
            
            if tiempo_transcurrido > time_limit:
                raise BadRequest(
                    f"Tiempo límite excedido ({tiempo_transcurrido:.1f}s de {time_limit}s)"
                )
        else:
            raise BadRequest("El cuestionario no tiene tiempo límite configurado")

        # Validación de estructura de respuestas
        if not answers or not all(isinstance(a, dict) and 'answer_id' in a and 'is_correct' in a for a in answers):
            raise BadRequest("Formato de respuestas inválido. Se espera lista de diccionarios con answer_id y is_correct")

        # Procesamiento de respuestas
        try:
            # Extraer y validar IDs de respuestas
            answer_ids = [a['answer_id'] for a in answers]
            
            # Verificar duplicados usando set para O(1) lookups
            unique_ids = set()
            for a in answers:
                if a['answer_id'] in unique_ids:
                    raise BadRequest(f"Respuesta duplicada para answer_id: {a['answer_id']}")
                unique_ids.add(a['answer_id'])

            # Crear respuestas con validación de tipos
            new_answers = []
            for answer in answers:
                if not isinstance(answer['is_correct'], bool):
                    raise BadRequest(f"Valor is_correct inválido para answer_id {answer['answer_id']}")
                    
                new_answers.append(
                    CompetitionQuizAnswer(
                        competition_quiz_id=competition_quiz_id,
                        participant_id=participant_id,
                        answer_id=answer['answer_id'],
                        is_correct=answer['is_correct'],
                        question_id=answer.get('question_id')  # Si viene del gateway
                    )
                )

            # Transacción atómica
            db.session.bulk_save_objects(new_answers)
            participante_en_cuestionario.end_time = time_finish
            
            # Actualizar puntaje
           
            tiempo_total = (participante_en_cuestionario.end_time - participante_en_cuestionario.start_time).total_seconds()
        
            correctas = sum(a['is_correct'] for a in answers)
            tiempo_no_utilizado = time_limit - tiempo_total
            puntaje = correctas * tiempo_no_utilizado
            participante_en_cuestionario.score = puntaje 
            db.session.commit()

        except SQLAlchemyError as e:
            db.session.rollback()
            raise BadRequest(f"Error de base de datos: {str(e)}")

        
        return {
            "competition_id": competition_id,
            "participant_id": participant_id,
            "quiz_id": cuestionario_en_competencia.quiz_id,
            "summary": {
                "correct_answers": sum(a['is_correct'] for a in answers),
                "score": participante_en_cuestionario.score,
                "time_spent": f"{tiempo_total:.2f}s",
                "time_limit": f"{time_limit}s"
            },
            "answers": [{
                "answer_id": a.answer_id,
                "is_correct": a.is_correct,
                "question_id": a.question_id
            } for a in new_answers]
        }
    @staticmethod
    def get_by_user_and_quiz(competition_quiz_id, participant_id):
        """
        Obtiene todas las respuestas de un usuario para un cuestionario específico
        """
        # Validar existencia de la participación
        participation = CompetitionQuizParticipants.query.filter_by(
            competition_quiz_id=competition_quiz_id,
            participant_id=participant_id
        ).first()

        if not participation:
            raise NotFound("Participant hasn't completed this quiz")

        # Obtener respuestas
        answers = CompetitionQuizAnswer.query.filter_by(
            competition_quiz_id=competition_quiz_id,
            participant_id=participant_id
        ).all()

        return [answer.to_dict() for answer in answers]

    @staticmethod
    def get_all_for_quiz(competition_quiz_id, page=1, per_page=50):
        """
        Obtiene todas las respuestas de todos los participantes para un cuestionario
        """
        # Validar existencia del cuestionario
        if not CompetitionQuiz.query.get(competition_quiz_id):
            raise NotFound("Competition quiz not found")

        # Consulta paginada
        query = CompetitionQuizAnswer.query.filter_by(
            competition_quiz_id=competition_quiz_id
        ).order_by(CompetitionQuizAnswer.created_at.asc())

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            "answers": [answer.to_dict() for answer in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        } 
    @staticmethod
    def get_complete_quiz_by_user(competition_quiz_id, participant_id):
        """
        Obtiene los datos del cuestionario de un participante solo si ya lo ha finalizado.
        """
        participante_en_cuestionario = CompetitionQuizParticipants.query.filter_by(
            competition_quiz_id=competition_quiz_id,
            participant_id=participant_id
        ).first()

        if not participante_en_cuestionario:
            raise NotFound(f"Participant {participant_id} is not registered in quiz {competition_quiz_id}.")

        if not participante_en_cuestionario.end_time:
            raise BadRequest(f"Participant {participant_id} has not finished quiz {competition_quiz_id} yet.")

        # Obtener datos del quiz y respuestas si aplicable (puedes extender esto según la estructura de datos)
        response = {
            "competition_quiz_participant_id": participante_en_cuestionario.id,
            "competition_id": participante_en_cuestionario.competition_quiz.competition_id,
            "participant_id": participante_en_cuestionario.participant_id,
            "quiz_id": participante_en_cuestionario.competition_quiz.quiz_id,
            "start_time": participante_en_cuestionario.start_time.isoformat() if participante_en_cuestionario.start_time else None,
            "end_time": participante_en_cuestionario.end_time.isoformat() if participante_en_cuestionario.end_time else None
        }

        return response

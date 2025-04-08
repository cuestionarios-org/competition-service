import requests
from app.models import CompetitionQuizParticipants, CompetitionQuiz, CompetitionParticipant,CompetitionQuizAnswer
from extensions import db
from werkzeug.exceptions import BadRequest, NotFound
import datetime as dt
from datetime  import timezone
from sqlalchemy.exc import SQLAlchemyError
import os

# Construcción de la URL base del microservicio de competencias
QA_SERVICE_URL = 'http://' + os.getenv('QA_HOST', 'localhost') + ':' + os.getenv('QA_PORT', '5013')

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

    @staticmethod
    def _validate_question_with_answer_structure(question_with_answer_choice):
        if not question_with_answer_choice or not isinstance(question_with_answer_choice, list):
            raise BadRequest("Formato inválido: se espera una lista de respuestas.")

        for item in question_with_answer_choice:
            if not isinstance(item, dict) or 'answer_id' not in item or 'question_id' not in item:
                raise BadRequest(f"Cada respuesta debe tener 'answer_id' y 'question_id'. {item}")


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

    @staticmethod
    def _check_answer_correctness_bulk(answers):
        """
        Llama al microservicio de QA para obtener la respuesta correcta por pregunta.
        Devuelve un dict {question_id: correct_answer_id}
        """
        try:
            response = requests.post(
                f"{QA_SERVICE_URL}/answer/answers/check",
                json={"answers": answers},  # cada uno con question_id y answer_id
                timeout=5
            )
            response.raise_for_status()
            results = response.json().get("answers", [])

            return {
                str(item["question_id"]): item["correct_answer_id"]
                for item in results
            }
        except requests.RequestException as e:
            raise BadRequest(f"No se pudo validar respuestas: {str(e)}")


    @staticmethod
    def finish_quiz(competition_quiz_id, participant_id, question_with_answer_choice):
        """
        Registra el tiempo de finalización y guarda las respuestas validadas con su corrección.
        """
        try:
            time_finish = dt.datetime.now(timezone.utc)

            quiz = CompetitionQuizParticipantService._get_quiz_or_404(competition_quiz_id)
            competition_id = quiz.competition_id

            CompetitionQuizParticipantService._check_participant_in_competition(competition_id, participant_id)

            participante = CompetitionQuizParticipants.query.filter_by(
                competition_quiz_id=competition_quiz_id,
                participant_id=participant_id
            ).first()

            if not participante:
                raise BadRequest(f"Participant {participant_id} hasn't started this quiz.")

            if participante.end_time:
                raise BadRequest("Quiz already completed.")

            time_limit = quiz.time_limit
            if time_limit < 0:
                raise BadRequest(f"El cuestionario no tiene tiempo límite configurado {time_limit}")

            tiempo_transcurrido = (time_finish - participante.start_time).total_seconds()
            if time_limit != 0 and tiempo_transcurrido > time_limit:
                raise BadRequest(f"Tiempo límite excedido ({tiempo_transcurrido:.1f}s de {time_limit}s)")

            CompetitionQuizParticipantService._validate_question_with_answer_structure(question_with_answer_choice)

            # Validar duplicados
            unique_ids = set()
            for q in question_with_answer_choice:
                question_id = q['question_id']
                if question_id in unique_ids:
                    raise BadRequest(f"Pregunta duplicada para question_id: {question_id}")
                unique_ids.add(question_id)

            # Validar respuestas con el microservicio QA
            correct_map = CompetitionQuizParticipantService._check_answer_correctness_bulk(question_with_answer_choice)

            new_answers = []
            correctas = 0
            for q in question_with_answer_choice:
                question_id = q['question_id']
                user_answer_id = q['answer_id']
                correct_answer_id = correct_map.get(str(question_id))

                if correct_answer_id is None:
                    raise BadRequest(f"No se pudo validar la respuesta de la pregunta {question_id}")

                is_correct = user_answer_id == correct_answer_id
                if is_correct:
                    correctas += 1

                new_answers.append(
                    CompetitionQuizAnswer(
                        competition_quiz_id=competition_quiz_id,
                        participant_id=participant_id,
                        answer_id=user_answer_id,
                        is_correct=is_correct,
                        question_id=question_id
                    )
                )

            # raise BadRequest(f"Error al guardar la respuesta: {new_answers}")
            # Guardar respuestas y finalizar quiz
            db.session.bulk_save_objects(new_answers)
            participante.end_time = time_finish

            tiempo_no_utilizado = time_limit - tiempo_transcurrido
            participante.score = correctas * tiempo_no_utilizado

            db.session.commit()

            return {
                "competition_id": competition_id,
                "participant_id": participant_id,
                "quiz_id": quiz.quiz_id,
                "summary": {
                    "correct_answers": correctas,
                    "score": participante.score,
                    "time_spent": f"{tiempo_transcurrido:.2f}s",
                    "time_limit": f"{time_limit}s"
                },
                "answers": [{
                    "question_id": a.question_id,
                    "answer_id": a.answer_id,
                    "is_correct": a.is_correct
                } for a in new_answers]
            }

        except (SQLAlchemyError, BadRequest, NotFound) as e:
            db.session.rollback()
            raise e
        except Exception as e:
            db.session.rollback()
            raise BadRequest(f"Unexpected error while finishing quiz: {str(e)}")

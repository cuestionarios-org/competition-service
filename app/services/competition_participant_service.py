from app.models import CompetitionParticipant
from app.models import Competition, CompetitionQuiz, CompetitionQuizParticipants
from app.utils.lib.constants import CompetitionQuizStatus
from extensions import db
from werkzeug.exceptions import BadRequest, NotFound
from sqlalchemy import desc

from sqlalchemy import select, func

class CompetitionParticipantService:
    @staticmethod
    def add_participant_to_competition(competition_id, participant_id):
        """
        Inscribe un participante en una competencia.
        :param competition_id: ID de la competencia.
        :param participant_id: ID del participante.
        :return: Instancia de la inscripción creada.
        """
        competition = Competition.query.get(competition_id)
        if not competition:
            raise NotFound(f"Competition with ID {competition_id} not found.")

        if competition.participant_limit > 0 and len(competition.participants) >= competition.participant_limit:
            raise BadRequest("Participant limit reached for this competition.")

        if CompetitionParticipant.query.filter_by(competition_id=competition_id, participant_id=participant_id).first():
            raise BadRequest(f"Participant {participant_id} is already registered in competition {competition_id}.")

        participant = CompetitionParticipant(competition_id=competition_id, participant_id=participant_id)
        db.session.add(participant)
        db.session.commit()
        return participant

    @staticmethod
    def remove_participant_from_competition(competition_id, participant_id):
        """
        Elimina un participante de una competencia.
        :param competition_id: ID de la competencia.
        :param participant_id: ID del participante.
        :return: Ninguno.
        """
        participant = CompetitionParticipant.query.filter_by(competition_id=competition_id, participant_id=participant_id).first()
        if not participant:
            raise NotFound(f"Participant {participant_id} is not registered in competition {competition_id}.")

        db.session.delete(participant)
        db.session.commit()

    @staticmethod
    def get_competition_ranking(competition_id):
        """
        Obtiene el ranking de participantes en una competencia, ordenado por puntaje descendente.
        :param competition_id: ID de la competencia.
        :return: Lista de participantes ordenados por puntaje.
        """
        competition = Competition.query.get(competition_id)
        if not competition:
            raise NotFound(f"Competition with ID {competition_id} not found.")

        ranking = CompetitionParticipant.query.filter_by(competition_id=competition_id  ) \
            .order_by(desc(CompetitionParticipant.score)).all()

        return [participant.to_dict() for participant in ranking]
    

    @staticmethod
    def get_competition_ranking_with_quizzes_computables(competition_id):
        """
        Obtiene el ranking de participantes en una competencia, ordenado por puntaje descendente,
        e incluye los quizzes computables con la lista de usuarios y sus puntajes por quiz.
        :param competition_id: ID de la competencia.
        :return: JSON con posiciones y quizzes computables.
        """
        competition = Competition.query.get(competition_id)
        if not competition:
            raise NotFound(f"Competition with ID {competition_id} not found.")

        # Filtrar los quizzes que son computables
        computable_quizzes = [
            {"id": quiz.id, "status": quiz.status}
            for quiz in competition.quizzes if quiz.status == "COMPUTABLE"
        ]

        # Obtener el ranking general de la competencia basado en el score total
        ranking = CompetitionParticipant.query.filter_by(competition_id=competition_id) \
            .order_by(desc(CompetitionParticipant.score)).all()

        # Construir la estructura de datos con los puntajes de los participantes en cada quiz computable
        quizzes_data = []

        for quiz in computable_quizzes:
            quiz_id = quiz["id"]
            
            participantes_quiz = (
                CompetitionQuizParticipants.query
                .filter_by(competition_quiz_id=quiz_id)
                .order_by(desc(CompetitionQuizParticipants.score_competition))
                .all()
            )

            # Estructura de datos con id del quiz y lista de participantes con sus puntajes
            quizzes_data.append({
                "id": quiz_id,
                "participantes": [
                    {
                        "participant_id": p.participant_id,
                        "score_competition": p.score_competition,
                        "start_time": p.start_time.isoformat() if p.start_time else None,
                        "end_time": p.end_time.isoformat() if p.end_time else None,
                        "score": p.score
                    }
                    for p in participantes_quiz
                ]
            })

        response = {
            "posiciones": [participant.to_dict() for participant in ranking],
            "quizzes": quizzes_data
        }
        
        return response

    
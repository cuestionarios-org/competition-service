from app.models import CompetitionParticipant
from app.models import Competition
from extensions import db
from werkzeug.exceptions import BadRequest, NotFound

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

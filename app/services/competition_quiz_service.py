from app.models import CompetitionQuiz
from extensions import db
from werkzeug.exceptions import BadRequest, NotFound

class CompetitionQuizService:
    @staticmethod
    def add_quiz_to_competitionNOSEUSA(competition_id, quiz_id):
        """
        Asocia un quiz a una competencia.
        :param competition_id: ID de la competencia.
        :param quiz_id: ID del quiz.
        :return: Instancia de la asociación creada.
        """
        if CompetitionQuiz.query.filter_by(competition_id=competition_id, quiz_id=quiz_id).first():
            raise BadRequest(f"Quiz {quiz_id} is already associated with competition {competition_id}.")

        competition_quiz = CompetitionQuiz(competition_id=competition_id, quiz_id=quiz_id)
        db.session.add(competition_quiz)
        db.session.commit()
        return competition_quiz

    @staticmethod
    def remove_quiz_from_competitionNOSEUSA(competition_id, quiz_id):
        """
        Elimina un quiz de una competencia.
        :param competition_id: ID de la competencia.
        :param quiz_id: ID del quiz.
        :return: Ninguno.
        """
        competition_quiz = CompetitionQuiz.query.filter_by(competition_id=competition_id, quiz_id=quiz_id).first()
        if not competition_quiz:
            raise NotFound(f"Quiz {quiz_id} is not associated with competition {competition_id}.")

        db.session.delete(competition_quiz)
        db.session.commit()

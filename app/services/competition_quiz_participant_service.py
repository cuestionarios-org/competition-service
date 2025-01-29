from app.models import CompetitionQuizParticipants, CompetitionQuiz, CompetitionParticipant
from extensions import db
from werkzeug.exceptions import BadRequest, NotFound
import datetime as dt

class CompetitionQuizParticipantService:
    @staticmethod
    def add_participant_to_quiz(competition_quiz_id, participant_id):
        """
        Inscribe un participante en un quiz de la competencia.
        :param competition_quiz_id: ID del quiz en la competencia.
        :param participant_id: ID del participante.
        :return: Instancia de la inscripción creada.
        """
        competition_quiz = CompetitionQuiz.query.get(competition_quiz_id)
        if not competition_quiz:
            raise NotFound(f"Competition quiz with ID {competition_quiz_id} not found.")

        if CompetitionQuizParticipants.query.filter_by(competition_quiz_id=competition_quiz_id, participant_id=participant_id).first():
            raise BadRequest(f"Participant {participant_id} is already registered in quiz {competition_quiz_id}.")

        participant = CompetitionQuizParticipants(competition_quiz_id=competition_quiz_id, participant_id=participant_id)
        db.session.add(participant)
        db.session.commit()
        return participant

    @staticmethod
    def start_quiz(competition_quiz_id, participant_id):
        """
        Registra el tiempo de inicio cuando un participante comienza el quiz.
        """

        # obtener el id de la competencia
        cuestionario_en_competencia = CompetitionQuiz.query.filter_by(id=competition_quiz_id).first()
        competition_id = cuestionario_en_competencia.competition_id

        # validar que el usuario este inscripto en la competencia
        participante_en_competencia = CompetitionParticipant.query.filter_by(competition_id=competition_id, participant_id=participant_id).first()      

        if not participante_en_competencia:
            raise NotFound(f"Participant {participant_id} is not registered in competition {competition_id}.")
        
        # ESTA INSCRIPTO >> validar que el cuestionario no este ya iniciado por el usuario
        participante_en_cuestionario = CompetitionQuizParticipants.query.filter_by(competition_quiz_id=competition_quiz_id, participant_id=participant_id).first()
        if participante_en_cuestionario != None:
            raise BadRequest(f"Participant {participant_id} is already registered in quiz {competition_quiz_id} for this competition {competition_id}.")  

        """
        TODO: 
        quizas validar el estado del cuestionario mas adelante
        chequear tiempos inicial y final del cuestionario
        """

        # Damos de alta el usuario en este cuestionario, comienza a correr el tiempo.
        participante_alta_en_cuestionario = CompetitionQuizParticipants(
            competition_quiz_id=competition_quiz_id, 
            participant_id=participant_id,
            start_time = db.func.now()
            )
        db.session.add(participante_alta_en_cuestionario)
        db.session.commit()
        # Retornamos el participante añadido a la fila y otro datos
        # con estos datos el gateway sabra formar el json para servir al cliente.
        response = {
            "competition_id": competition_id,
            "participant_id": participant_id,
            "start_time": participante_alta_en_cuestionario.start_time.isoformat() if participante_alta_en_cuestionario.start_time else None,
            "competition_quiz_participant_id": participante_alta_en_cuestionario.id,
            "quiz_id": cuestionario_en_competencia.quiz_id
        }
        return response

    @staticmethod
    def finish_quiz(competition_quiz_id, participant_id):
        """
        Registra el tiempo de finalización cuando un participante envía el quiz.
        """
        # guardamos el tiempo antes que nada
        time_finish = db.func.now()
        # obtener el id de la competencia
        cuestionario_en_competencia = CompetitionQuiz.query.filter_by(id=competition_quiz_id).first()
        competition_id = cuestionario_en_competencia.competition_id

        # validar que el usuario este inscripto en la competencia
        participante_en_competencia = CompetitionParticipant.query.filter_by(competition_id=competition_id, participant_id=participant_id).first()      

        if not participante_en_competencia:
            raise NotFound(f"Participant {participant_id} is not registered in competition {competition_id}.")
        
        # ESTA INSCRIPTO >> validar que el cuestionario este  iniciado por el usuario
        participante_en_cuestionario = CompetitionQuizParticipants.query.filter_by(competition_quiz_id=competition_quiz_id, participant_id=participant_id).first()
        if participante_en_cuestionario == None:
            raise BadRequest(f"Participant {participant_id} is not registered in quiz {competition_quiz_id} for this competition {competition_id}.")  


        
        """
        TODO: 
        quizas validar el estado del cuestionario mas adelante
        chequear tiempos inicial y final del cuestionario
        """
        
        if participante_en_cuestionario.start_time == None:
            raise BadRequest(f"Participant {participant_id} has not started quiz {competition_quiz_id} for this competition {competition_id}.")
        if participante_en_cuestionario.end_time != None:
            raise BadRequest(f"Participant {participant_id} has already finished quiz {competition_quiz_id} for this competition {competition_id}.")
        
        participante_en_cuestionario.end_time = time_finish
        db.session.commit()


        # TODO: Recibir las repuestas y agregarlas, mas sacar el calculo del puntaje

        # Retornamos el participante añadido a la fila y otro datos
        # con estos datos el gateway sabra formar el json para servir al cliente.
        response = {
            "competition_id": competition_id,
            "participant_id": participant_id,
            "start_time": participante_en_cuestionario.start_time.isoformat() if participante_en_cuestionario.start_time else None,
            "end_time": participante_en_cuestionario.end_time.isoformat() if participante_en_cuestionario.end_time else None,
            "competition_quiz_participant_id": participante_en_cuestionario.id,
            "quiz_id": cuestionario_en_competencia.quiz_id
        }
        return response
    
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

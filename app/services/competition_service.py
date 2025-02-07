from app.models import Competition, CompetitionQuiz
from extensions import db
from werkzeug.exceptions import BadRequest, NotFound
from sqlalchemy.orm import joinedload
from datetime import datetime


class CompetitionService:
    @staticmethod
    def get_all_competitions():
        """
        Recupera todas las competencias.
        :return: Lista de instancias de competencias.
        """
        competitions = (Competition.query
        .options(joinedload(Competition.quizzes), joinedload(Competition.participants))
        .all())
        return competitions

    @staticmethod
    def create_competition(data):
        """
        Crea una nueva competencia con estructura extendida de quizzes.
        """
        required_fields = ['title', 'start_date', 'end_date', 'created_by']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f"Missing required field: {field}")
        
        # Validar fechas principales
        try:
            start_date = datetime.fromisoformat(data['start_date'])
            end_date = datetime.fromisoformat(data['end_date'])
        except ValueError:
            raise BadRequest("Formato de fecha inválido. Usar ISO 8601")

        competition = Competition(
            title=data['title'],
            description=data.get('description', ''),
            start_date=start_date,
            end_date=end_date,
            created_by=data['created_by'],
            participant_limit=data.get('participant_limit', 0),
            currency_cost=data.get('currency_cost', 100),
            ticket_cost=data.get('ticket_cost', 0),
            credit_cost=data.get('credit_cost', 0),
        )

        db.session.add(competition)
        db.session.flush()

        # Procesar quizzes con nueva estructura
        if 'quizzes' in data:
            for quiz_data in data['quizzes']:
                CompetitionService.add_quiz_to_competition(
                    competition_id=competition.id,
                    quiz_data=quiz_data
                )

        db.session.commit()
        return competition

    @staticmethod
    def update_competition(competition_id, data):
        """
        Actualiza los detalles de una competencia.
        :param competition_id: ID de la competencia.
        :param data: Diccionario con los datos actualizados.
        :return: Instancia de la competencia actualizada.
        """
        competition = Competition.query.get_or_404(competition_id)
        if not competition:
            raise NotFound(f"Competition with ID {competition_id} not found.")

        # Actualización de los campos básicos de la competencia (title, description, fechas, costos, etc.)
        competition.title = data.get('title', competition.title)
        competition.description = data.get('description', competition.description)
        competition.start_date = data.get('start_date', competition.start_date)
        competition.end_date = data.get('end_date', competition.end_date)    
        competition.participant_limit = data.get('participant_limit', competition.participant_limit)
        competition.currency_cost = data.get('currency_cost', competition.currency_cost)
        competition.ticket_cost = data.get('ticket_cost', competition.ticket_cost)
        competition.credit_cost = data.get('credit_cost', competition.credit_cost)
        competition.modified_by = data.get('modified_by', competition.modified_by)

        # Cambiar el estado si se proporciona uno nuevo
        new_state = data.get('state')
        if new_state and new_state != competition.state:
            try:
                competition.set_state(new_state)
            except ValueError as e:
                raise ValueError(f"No se pudo actualizar el estado: {str(e)}")
        
        # Manejo de cuestionarios asociados a la competencia
        if 'quizzes' in data:
            current_quizzes = {q.quiz_id: q for q in competition.quizzes}
            
            # Recorrer los quizzes enviados y actualizar o agregar según corresponda
            for quiz_data in data['quizzes']:
                quiz_id = quiz_data['quiz_id']
                
                if quiz_id in current_quizzes:
                    # Actualizar quiz existente
                    quiz = current_quizzes[quiz_id]
                    
                    # Solo actualizar los campos que están presentes en los datos
                    quiz.start_time = datetime.fromisoformat(quiz_data.get('start_time')) if quiz_data.get('start_time') else quiz.start_time
                    quiz.end_time = datetime.fromisoformat(quiz_data.get('end_time')) if quiz_data.get('end_time') else quiz.end_time
                    quiz.time_limit = quiz_data.get('time_limit', quiz.time_limit)
                else:
                    # Agregar nuevo quiz
                    CompetitionService.add_quiz_to_competition(
                        competition_id=competition.id,
                        quiz_data=quiz_data
                    )

            # Eliminar quizzes no presentes en los nuevos datos
            current_ids = {q.quiz_id for q in competition.quizzes}
            new_ids = {q['quiz_id'] for q in data['quizzes']}
            to_remove = current_ids - new_ids
            
            for quiz_id in to_remove:
                CompetitionService.remove_quiz_from_competition(competition.id, quiz_id)

        db.session.commit()
        return competition
    @staticmethod
    def get_competition(competition_id):
        """
        Recupera una competencia por ID.
        :param competition_id: ID de la competencia.
        :return: Instancia de la competencia.
        """
        competition = Competition.query.get(competition_id)
        if not competition:
            raise NotFound(f"Competition with ID {competition_id} not found.")
        return competition
    

    @staticmethod
    def add_quiz_to_competition(competition_id, quiz_data):
        """
        Agrega un cuestionario con parámetros extendidos.
        """
        try:
            competition = Competition.query.get_or_404(competition_id)
            
            # Validar estado de la competencia
            if competition.state != 'preparacion':
                raise ValueError(f"No se pueden agregar quizzes en estado '{competition.state}'")
            
            # Validar datos del quiz
            if 'quiz_id' not in quiz_data:
                raise ValueError("Falta quiz_id en los datos del cuestionario")
            
            # Convertir fechas
            start_time = datetime.fromisoformat(quiz_data.get('start_time')) if quiz_data.get('start_time') else None
            end_time = datetime.fromisoformat(quiz_data.get('end_time')) if quiz_data.get('end_time') else None
            
            # Validar límite de tiempo
            time_limit = quiz_data.get('time_limit', 0)
            if time_limit < 0:
                raise ValueError("El tiempo límite no puede ser negativo")
            
            # Validar duplicados
            if any(q.quiz_id == quiz_data['quiz_id'] for q in competition.quizzes):
                raise ValueError(f"El quiz {quiz_data['quiz_id']} ya está asociado")
            
            # Crear registro
            competition_quiz = CompetitionQuiz(
                competition_id=competition_id,
                quiz_id=quiz_data['quiz_id'],
                start_time=start_time,
                end_time=end_time,
                time_limit=time_limit
            )
            
            db.session.add(competition_quiz)
            return competition_quiz
            
        except ValueError as e:
            db.session.rollback()
            raise BadRequest(str(e))
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al agregar quiz: {str(e)}")

    @staticmethod
    def remove_quiz_from_competition(competition_id, quiz_id):
        """
        Elimina un cuestionario de una competencia.
        """
        competition = Competition.query.get_or_404(competition_id)
        competition_quiz_id = CompetitionQuiz.query.filter_by(competition_id=competition_id, quiz_id=quiz_id).first()
        if not competition_quiz_id:
            raise ValueError(f"El cuestionario {quiz_id} no está asociado a la competencia {competition_id}.")
        db.session.delete(competition_quiz_id)
        db.session.commit()
        return competition


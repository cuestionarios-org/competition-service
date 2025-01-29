from app.models import Competition, CompetitionQuiz
from extensions import db
from werkzeug.exceptions import BadRequest, NotFound
from sqlalchemy.orm import joinedload


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
        Crea una nueva competencia.
        :param data: Diccionario con los datos de la competencia.
        :return: Instancia de la competencia creada.
        """
        required_fields = ['title', 'start_date', 'end_date', 'created_by']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f"Missing required field: {field}")

        competition = Competition(
            title=data['title'],
            description=data.get('description', ''),
            start_date=data['start_date'],
            end_date=data['end_date'],
            created_by=data['created_by'],
            participant_limit=data.get('participant_limit', 0),
            currency_cost=data.get('currency_cost', 100),
            ticket_cost=data.get('ticket_cost', 0),
            credit_cost=data.get('credit_cost', 0),
        )

        db.session.add(competition)
        db.session.flush()  # Obtener el ID de la competencia recién creada

        # Validar y asociar cuestionarios a la competencia
        if 'quizzes' in data:
            for quiz_id in data['quizzes']:
                CompetitionService.add_quiz_to_competition(competition.id, quiz_id)
        #Participantes al crear siempre sera vacio.

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
            new_quizzes_ids = set(data['quizzes'])

            # Obtener los cuestionarios actuales asociados a la competencia
            current_quizzes_ids = {q.quiz_id for q in competition.quizzes}
        

            print(new_quizzes_ids, current_quizzes_ids)
            # Identificar cuestionarios a agregar y a eliminar
            to_add = new_quizzes_ids - current_quizzes_ids
            to_remove = current_quizzes_ids - new_quizzes_ids

            # Validar y agregar nuevos cuestionarios
            # No hay como validar aqui los ids, deben ya estar validados en gateway ya que de aca no se peticionara al ms de quiz
            
            if to_add:
                for quiz_id in to_add:
                    CompetitionService.add_quiz_to_competition(competition.id, quiz_id)

            # Eliminar cuestionarios asociados a la competencia
            if to_remove:
                for quiz_id in to_remove:
                    CompetitionService.remove_quiz_from_competition(competition.id, quiz_id)

        # Actualizar la competencia en la base de datos
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
    def add_quiz_to_competition(competition_id, quiz_id):
        """
        Agrega un cuestionario a una competencia. Verifica el estado a un cuestionario si la transición es válida y la pregunta no está ya asociada.
        """
        try:
            # Obtener la competencia y los cuestionarios
            competition = Competition.query.get_or_404(competition_id)
            # quiz = CompetitionQuiz.query.get_or_404(quiz_id)
            
            # Verificar el estado de la competencia
            if competition.state != 'preparacion':
                raise ValueError(f"No se puede agregar un cuestionario a la competencia en estado '{competition.state}'. El estado debe ser 'preparcion'.")

            # Verificar si el cuestionario ya está asociado a la competencia
            if quiz_id in competition.quizzes:
                raise ValueError(f"El cuestionario con ID:  '{quiz_id}' ya está asociada a esta competencia.")
            
            # Agregar el cuestionario a la competencia 
            competition_quiz = CompetitionQuiz(competition_id=competition_id, quiz_id=quiz_id)
            db.session.add(competition_quiz)
            db.session.commit()

            return competition
        
        except ValueError as e:
            # Si hay un error de validación, se puede manejar aquí
            db.session.rollback()  # Hacemos rollback en caso de error
            raise ValueError(f"Error al agregar el cuestionario: {str(e)}")
        
        except Exception as e:
            # Capturamos cualquier otro tipo de excepción
            db.session.rollback()
            raise Exception(f"Ocurrió un error inesperado al agregar un cuestionario: {str(e)}")


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

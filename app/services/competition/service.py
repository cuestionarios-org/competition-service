from app.models import Competition
from extensions import db
from werkzeug.exceptions import BadRequest, NotFound
from sqlalchemy.orm import joinedload
from dateutil import parser

# Helpers para la lógica de quizzes
from app.services.competition.helpers.quiz_updater import update_quizzes
from app.services.competition.helpers.quiz_builder import build_quiz_entry


class CompetitionService:
    # ----------------------------------------------------
    @staticmethod
    def get_all_competitions():
        """
        Recupera todas las competencias disponibles en la base de datos,
        incluyendo la relación con quizzes y participantes.

        :return: Lista de instancias de Competition.
        """
        competitions = (
            Competition.query
            .options(joinedload(Competition.quizzes), joinedload(Competition.participants))  # Carga relaciones con eficiencia
            .all()
        )
        return competitions

    # ----------------------------------------------------
    @staticmethod
    def create_competition(data):
        """
        Crea una nueva competencia y opcionalmente asocia quizzes.

        :param data: Diccionario con los datos de la competencia.
        :return: Instancia de Competition creada.
        """
        required_fields = ['title', 'start_date', 'end_date', 'created_by']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f"Falta el campo obligatorio: {field}")

        # Validación de fechas en formato ISO 8601
        try:
            start_date = parser.isoparse(data['start_date'])
            end_date = parser.isoparse(data['end_date'])
        except (ValueError, TypeError):
            raise BadRequest(f"Formato de fecha inválido. Usar ISO 8601.")

        # Crear nueva instancia de Competition
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
        db.session.flush()  # Necesario para obtener el ID antes del commit

        # Procesar y asociar quizzes si vienen incluidos en el payload
        if 'quizzes' in data:
            for quiz_data in data['quizzes']:
                CompetitionService.add_quiz_to_competition(
                    competition_id=competition.id,
                    quiz_data=quiz_data
                )

        db.session.commit()
        return competition

    # ----------------------------------------------------
    @staticmethod
    def get_competition(competition_id):
        """
        Busca una competencia por su ID.

        :param competition_id: ID de la competencia.
        :return: Instancia de Competition.
        :raises NotFound: Si no se encuentra la competencia.
        """
        competition = Competition.query.get(competition_id)

        if not competition:
            raise NotFound(f"Competition con ID {competition_id} no encontrada.")
        return competition

    # ----------------------------------------------------
    @staticmethod
    def add_quiz_to_competition(competition_id, quiz_data):
        """
        Agrega un quiz existente a una competencia si no está ya asociado.

        :param competition_id: ID de la competencia.
        :param quiz_data: Diccionario con datos del quiz (debe incluir quiz_id).
        :return: Objeto de relación entre competencia y quiz.
        :raises BadRequest: Si el quiz ya está asociado o hay otro error.
        """
        try:
            competition = Competition.query.get_or_404(competition_id)

            # Validar que el quiz no esté duplicado en esta competencia
            if any(q.quiz_id == quiz_data['quiz_id'] for q in competition.quizzes):
                raise ValueError(f"El quiz {quiz_data['quiz_id']} ya está asociado a esta competencia.")

            quiz = build_quiz_entry(competition, quiz_data)
            db.session.add(quiz)
            db.session.commit()
            return quiz

        except Exception as e:
            db.session.rollback()
            raise BadRequest(f"Ocurrió un error al agregar el quiz: {str(e)}")

    # ----------------------------------------------------
    @staticmethod
    def update_competition(competition_id, data):
        """
        Actualiza los datos de una competencia existente, incluyendo quizzes.

        :param competition_id: ID de la competencia.
        :param data: Diccionario con los campos a actualizar.
        :return: Instancia actualizada de Competition.
        :raises ValueError: Si la competencia no existe.
        """
        competition = Competition.query.get(competition_id)
        if not competition:
            raise ValueError("Competencia no encontrada.")

        # Actualización de campos individuales si están presentes en el payload
        if 'title' in data:
            competition.title = data['title']

        if 'start_date' in data:
            competition.start_date = parser.isoparse(data['start_date'])

        if 'end_date' in data:
            competition.end_date = parser.isoparse(data['end_date'])

        if 'state' in data:
            competition.state = data['state']

        # Actualización de quizzes usando helper
        if 'quizzes' in data:
            update_quizzes(competition, data['quizzes'])

        db.session.commit()
        return competition

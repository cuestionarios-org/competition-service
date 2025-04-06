from app.models import Competition, CompetitionQuiz
from extensions import db
from werkzeug.exceptions import BadRequest, NotFound
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone
from dateutil import parser

class CompetitionService:
    # ----------------------------------------------------
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

    # ----------------------------------------------------
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

            start_date = parser.isoparse(data['start_date'])
            end_date = parser.isoparse(data['end_date'])
        except ValueError:
            raise BadRequest(f"Formato de fecha inválido. Usar ISO 8601 start_date !!!!>> {data['start_date']}")

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
        # quizzes es un array de objetos de los cuestionarios
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
        Recupera una competencia por ID.
        :param competition_id: ID de la competencia.
        :return: Instancia de la competencia.
        """
        competition = Competition.query.get(competition_id)


        if not competition:
            raise NotFound(f"Competition with ID {competition_id} not found.")
        return competition
    
    # ----------------------------------------------------
    @staticmethod
    def add_quiz_to_competition(competition_id, quiz_data):
        try:
            competition = Competition.query.get_or_404(competition_id)

            if any(q.quiz_id == quiz_data['quiz_id'] for q in competition.quizzes):
                raise ValueError(f"El quiz {quiz_data['quiz_id']} ya está asociado a esta competencia.")

            quiz = CompetitionService.__build_quiz_entry(competition, quiz_data)
            db.session.add(quiz)
            db.session.commit()
            return quiz

        except Exception as e:
            db.session.rollback()
            raise BadRequest(str(e))
    
    # ----------------------------------------------------
    @staticmethod
    def update_competition(competition_id, data):
        """
        Actualiza los detalles de una competencia, incluyendo sus cuestionarios asociados.
        """
        competition = Competition.query.get_or_404(competition_id)

        # Actualización básica de campos
        competition.title = data.get('title', competition.title)
        competition.description = data.get('description', competition.description)
        competition.start_date = data.get('start_date', competition.start_date)
        competition.end_date = data.get('end_date', competition.end_date)    
        competition.participant_limit = data.get('participant_limit', competition.participant_limit)
        competition.currency_cost = data.get('currency_cost', competition.currency_cost)
        competition.ticket_cost = data.get('ticket_cost', competition.ticket_cost)
        competition.credit_cost = data.get('credit_cost', competition.credit_cost)
        competition.modified_by = data.get('modified_by', competition.modified_by)

        # Actualización de estado
        new_state = data.get('state')
        if new_state and new_state != competition.state:
            competition.set_state(new_state)

        # Actualización de quizzes
        if 'quizzes' in data:
            CompetitionService.__process_quizzes_update(competition, data['quizzes'])

        db.session.commit()
        return competition

    # ----------------------------------------------------
    @staticmethod
    def __process_quizzes_update(competition, incoming_quizzes_data):
        """
        Clasifica y procesa los cuestionarios: agregar, actualizar, eliminar.
        """
        existing_quizzes = {q.quiz_id: q for q in competition.quizzes}
        incoming_quiz_ids = {q['quiz_id'] for q in incoming_quizzes_data}
        existing_quiz_ids = set(existing_quizzes.keys())

        # Clasificación
        quizzes_to_add = [
            q for q in incoming_quizzes_data
            if q['quiz_id'] not in existing_quiz_ids
        ]

        modifying_keys = {'start_time', 'end_time', 'time_limit'}
        quizzes_to_update = [
            q for q in incoming_quizzes_data
            if q['quiz_id'] in existing_quiz_ids and modifying_keys.intersection(q.keys())
        ]

        quizzes_to_remove = [
            existing_quizzes[qid]
            for qid in existing_quiz_ids - incoming_quiz_ids
        ]

        # Procesar agregados
        for quiz_data in quizzes_to_add:
            quiz = CompetitionService.__build_quiz_entry(competition, quiz_data)
            db.session.add(quiz)

        # Procesar actualizaciones
        for quiz_data in quizzes_to_update:
            existing_quiz = existing_quizzes[quiz_data['quiz_id']]
            CompetitionService.__build_quiz_entry(
                competition,
                quiz_data,
                existing_quiz=existing_quiz
            )

        # Procesar eliminaciones
        for quiz in quizzes_to_remove:
            CompetitionService.__validate_quiz_removal(competition, quiz)
            db.session.delete(quiz)


    # ---------------------------------------------------------------------
    @staticmethod
    def __validate_quiz_constraints(
        competition,
        quiz_id,
        start_time=None,
        end_time=None,
        existing_start_time=None,
        is_modifying=False,
        is_removal=False
    ):
        """
        Valida restricciones de fechas y estados para quizzes.
        """
        now = datetime.now(timezone.utc)

        competition_start = competition.start_date.astimezone(timezone.utc)
        competition_end = competition.end_date.astimezone(timezone.utc)

        # Validación de estado de competencia
        if is_removal:
            if competition.state not in {'preparacion', 'lista'}:
                raise ValueError(f"No se puede eliminar quizzes en estado '{competition.state}'.")
        elif is_modifying:
            if competition.state not in {'preparacion', 'lista', 'en curso'}:
                raise ValueError(f"No se pueden modificar quizzes cuando la competencia tiene estado '{competition.state}'.")
        else:
            if competition.state not in {'preparacion', 'lista', 'en curso'}:
                raise ValueError(f"No se pueden agregar quizzes en estado '{competition.state}'.")

        # Validación de fechas pasadas
        if existing_start_time and existing_start_time <= now:
            if is_modifying:
                raise ValueError(f"No se puede modificar el quiz '{quiz_id}' porque ya ha comenzado.")
            if is_removal:
                raise ValueError(f"No se puede eliminar el quiz '{quiz_id}' porque ya ha comenzado.")

        if start_time and start_time <= now:
            if is_modifying:
                raise ValueError(f"No se puede asignar una fecha de inicio en el pasado ({quiz_id}).")

        if start_time and start_time < competition_start:
            raise ValueError("La fecha de inicio del quiz no puede ser anterior a la de la competencia.")

        if end_time and end_time > competition_end:
            raise ValueError("La fecha de fin del quiz no puede ser posterior a la de la competencia.")

        if start_time and end_time and start_time > end_time:
            raise ValueError("La fecha de inicio no puede ser posterior a la de fin.")

    # ---------------------------------------------------------------------
    @staticmethod
    def __validate_quiz_removal(competition, quiz):
        """
        Valida si un quiz puede ser eliminado de la competencia.
        """
        CompetitionService.__validate_quiz_constraints(
            competition=competition,
            quiz_id=quiz.quiz_id,
            existing_start_time=quiz.start_time,
            is_removal=True
        )

    # ---------------------------------------------------------------------
    @staticmethod
    def __build_quiz_entry(competition, quiz_data, existing_quiz=None):
        """
        Construye o actualiza un objeto CompetitionQuiz con validaciones.
        """
        if 'quiz_id' not in quiz_data:
            raise ValueError("Falta quiz_id en los datos del cuestionario.")

        modifying_fields = any(
            key in quiz_data for key in ['start_time', 'end_time', 'time_limit']
        )

        # Parseo de fechas
        start_time = parser.isoparse(quiz_data.get('start_time')) if quiz_data.get('start_time') else None
        end_time = parser.isoparse(quiz_data.get('end_time')) if quiz_data.get('end_time') else None

        if start_time and start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time and end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        # Validaciones
        CompetitionService.__validate_quiz_constraints(
            competition=competition,
            quiz_id=quiz_data['quiz_id'],
            start_time=start_time,
            end_time=end_time,
            existing_start_time=existing_quiz.start_time if existing_quiz else None,
            is_modifying=bool(existing_quiz),
            is_removal=False
        )

        if quiz_data.get('time_limit', 0) < 0:
            raise ValueError("El tiempo límite no puede ser negativo.")

        quiz = existing_quiz if existing_quiz else CompetitionQuiz()
        quiz.quiz_id = quiz_data['quiz_id']
        quiz.start_time = start_time
        quiz.end_time = end_time
        quiz.time_limit = quiz_data.get('time_limit', 0)
        quiz.competition_id = competition.id

        return quiz


from extensions import db
from sqlalchemy.orm import validates, relationship
from datetime import datetime, timezone
from app.utils.lib.pretty import pretty_print_dict
from sqlalchemy.exc import SQLAlchemyError
from app.models.competition_quiz import CompetitionQuiz
from app.models.competition_participant import CompetitionParticipant

from app.utils.lib.formatting import safe_date_isoformat

class Competition(db.Model):
    __tablename__ = 'competitions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    state = db.Column(db.String(50), nullable=False, default='preparacion')
    created_by = db.Column(db.Integer, nullable=False)
    modified_by = db.Column(db.Integer)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    end_date = db.Column(db.DateTime(timezone=True), nullable=True)

    # Límite de participantes (0 significa sin límite)
    participant_limit = db.Column(db.Integer, nullable=False, default=0)

    # Coste de inscripción
    currency_cost = db.Column(db.Integer, nullable=False, default=100)
    ticket_cost = db.Column(db.Integer, nullable=False, default=0)
    credit_cost = db.Column(db.Integer, nullable=False, default=0)

    # Relaciones
    quizzes = relationship('CompetitionQuiz', back_populates='competition', cascade="all, delete-orphan")
    participants = relationship('CompetitionParticipant', back_populates='competition', cascade="all, delete-orphan")

    __table_args__ = (
        db.Index('idx_state_end_date', 'state', 'end_date'),  # Índice combinado
        db.CheckConstraint('participant_limit >= 0', name='check_participant_limit_positive'),
        db.CheckConstraint('currency_cost >= 0', name='check_currency_cost_positive'),
        db.CheckConstraint('ticket_cost >= 0', name='check_ticket_cost_positive'),
        db.CheckConstraint('credit_cost >= 0', name='check_credit_cost_positive'),
        db.CheckConstraint('start_date < end_date', name='check_valid_dates'),
    )

    # Validaciones
    @validates('state')
    def validate_state(self, key, value):
        allowed_states = ['preparacion', 'lista', 'en curso', 'cerrada', 'finalizada']
        if value not in allowed_states:
            raise ValueError(f"El estado '{value}' no es válido.")
        return value

    @validates('participant_limit')
    def validate_participant_limit(self, key, value):
        if value < 0:
            raise ValueError("El límite de participantes no puede ser negativo.")
        return value
    
    @validates('start_date', 'end_date')
    def validate_dates(self, key, value):
        if value is None:
            return None  # Permite valores nulos si nullable=True
        
        # Convertir strings a datetime
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(f"Formato inválido para {key}. Usar ISO 8601")
        
        # Forzar UTC si no tiene zona horaria
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        
        return value

    # Métodos
    def add_quiz(self, quiz_id):
        """
        Agrega un quiz a la competencia.
        """
        if CompetitionQuiz.query.filter_by(competition_id=self.id, quiz_id=quiz_id).first():
            raise ValueError(f"El quiz {quiz_id} ya está asociado a la competencia {self.id}.")
        new_quiz = CompetitionQuiz(competition_id=self.id, quiz_id=quiz_id)
        db.session.add(new_quiz)
        db.session.commit()

    def remove_quiz(self, quiz_id):
        """
        Elimina un quiz de la competencia.
        """
        quiz = CompetitionQuiz.query.filter_by(competition_id=self.id, quiz_id=quiz_id).first()
        if not quiz:
            raise ValueError(f"El quiz {quiz_id} no está asociado a la competencia {self.id}.")
        db.session.delete(quiz)
        db.session.commit()

    def add_participant(self, participant_id):
        """
        Inscribe un participante en la competencia.
        """
        if self.participant_limit > 0 and len(self.participants) >= self.participant_limit:
            raise ValueError("Se ha alcanzado el límite de participantes.")
        if CompetitionParticipant.query.filter_by(competition_id=self.id, participant_id=participant_id).first():
            raise ValueError(f"El participante {participant_id} ya está inscrito en la competencia {self.id}.")
        new_participant = CompetitionParticipant(competition_id=self.id, participant_id=participant_id)
        db.session.add(new_participant)
        db.session.commit()

    def remove_participant(self, participant_id):
        """
        Elimina un participante de la competencia.
        """
        participant = CompetitionParticipant.query.filter_by(competition_id=self.id, participant_id=participant_id).first()
        if not participant:
            raise ValueError(f"El participante {participant_id} no está inscrito en la competencia {self.id}.")
        db.session.delete(participant)
        db.session.commit()

    def set_state(self, new_state):
        """
        Cambiar el estado de la competencia considerando las transiciones válidas
        """
        valid_transitions = {
            'preparacion': ['lista'],
            'lista': ['en curso', 'cerrada'],
            'en curso': ['cerrada', 'finalizada'],
            'cerrada': ['finalizada'],
        }
        if new_state not in valid_transitions.get(self.state, []):
            raise ValueError(f"No se puede cambiar de {self.state} a {new_state}.")
        self.state = new_state

    def close_if_ended(self):
        """
        Verifica si la competencia debe ser cerrada según su fecha de finalización
        y realiza el cambio de estado dentro de una transacción segura.
        """
        if self.state in ['lista', 'en curso'] and dt.datetime.now(dt.timezone.utc) >= self.end_date:
            try:
                # Iniciar una transacción
                with db.session.begin_nested():
                    self.state = 'cerrada'
                    db.session.add(self)
                db.session.commit()
                print(f"Competencia {self.id} cerrada automáticamente.")
            except SQLAlchemyError as e:
                db.session.rollback()
                print(f"Error al cerrar la competencia {self.id}: {e}")
        else:
            print(f"No es necesario cerrar la competencia {self.id} en estado {self.state}.")

    def __repr__(self):
        pretty_print_dict(self.to_dict())
        return ""

    def to_dict(self):
       
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "state": self.state,
            "created_by": self.created_by,
            "modified_by": self.modified_by,
            "created_at": safe_date_isoformat(self.created_at),
            "updated_at": safe_date_isoformat(self.updated_at),
            "start_date": safe_date_isoformat(self.start_date),
            "end_date": safe_date_isoformat(self.end_date),
            "participant_limit": self.participant_limit,
            "currency_cost": self.currency_cost,
            "ticket_cost": self.ticket_cost,
            "credit_cost": self.credit_cost,
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "participants": [participant.to_dict() for participant in self.participants],
        }
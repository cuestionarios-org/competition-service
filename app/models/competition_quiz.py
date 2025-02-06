from extensions import db
from datetime import datetime, timezone
from app.utils.lib.formatting import safe_date_isoformat
from sqlalchemy.orm import validates

from app.utils.lib.constants import CompetitionQuizStatus


class CompetitionQuiz(db.Model):
    """
    Tabla intermedia para asociar competencias con los IDs de quizzes.
    """
    __tablename__ = 'competition_quizzes'

    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)  # Relación con Competitions
    quiz_id = db.Column(db.Integer, nullable=False)  # ID del quiz
    
    time_limit = db.Column(
        db.Integer, 
        nullable=True, 
        default=0,  # 0 = sin límite de tiempo
        comment="Duración máxima en segundos para completar el cuestionario"
    )

    processed = db.Column(
        db.Boolean,
        default=False,
        nullable=True,
        index=True,  # Para búsquedas eficientes
        comment="Indica si ya se procesaron los resultados"
    )

    status = db.Column(
        db.String(50), 
        nullable=False, 
        default=CompetitionQuizStatus.ACTIVO, 
        comment="Estado del cuestionario dentro de la competencia"
    )

    start_time = db.Column(db.DateTime(timezone=True), nullable=True)
    end_time = db.Column(db.DateTime(timezone=True), nullable=True)
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
    # Relación con Competition
    competition = db.relationship('Competition', back_populates='quizzes')
    # Relación con CompetitionQuizParticipants
    participants = db.relationship('CompetitionQuizParticipants', back_populates='competition_quiz')
    answers = db.relationship(
        'CompetitionQuizAnswer', 
        back_populates='competition_quiz', 
        cascade="all, delete-orphan"  # Elimina respuestas si se borra el quiz de la competencia
    )
    
    __table_args__ = (
        db.UniqueConstraint('competition_id', 'quiz_id', name='uq_competition_quiz'),  # Evita duplicados
        db.CheckConstraint('time_limit >= 0', name='check_time_limit_positive'),
    )

    # Validaciones
    @validates('status')
    def validate_status(self, key, value):
        """
        Validar que el estado proporcionado es válido.
        """
        if value not in CompetitionQuizStatus.values():
            raise ValueError(f"El estado '{value}' no es válido.")
        return value

    # Métodos

    def set_status(self, new_status):
        """
        Cambiar el estado de la competencia considerando las transiciones válidas.
        """
        valid_transitions = {
            CompetitionQuizStatus.ACTIVO: [CompetitionQuizStatus.COMPUTABLE],
            CompetitionQuizStatus.COMPUTABLE: [CompetitionQuizStatus.NO_COMPUTABLE],
            CompetitionQuizStatus.NO_COMPUTABLE: []  # No puede cambiar a otro estado
        }

        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(f"No se puede cambiar el estado de {self.status.value} a {new_status.value}.")
        
        self.status = new_status
    def __repr__(self):
        return f"<CompetitionQuiz Competition {self.competition_id} - Quiz {self.quiz_id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "competition_id": self.competition_id,
            "quiz_id": self.quiz_id,
            "time_limit": self.time_limit,
            "status": self.status.value,
            "start_time": safe_date_isoformat(self.start_time),
            "end_time": safe_date_isoformat(self.end_time),
            "created_at": safe_date_isoformat(self.created_at),
            "updated_at": safe_date_isoformat(self.updated_at),
        }

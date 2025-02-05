from extensions import db
from sqlalchemy.orm import validates
from datetime import datetime, timezone

class CompetitionQuizParticipants(db.Model):
    """
    Tabla intermedia para asociar los participantes a un quiz de una competencia.
    """
    __tablename__ = 'competition_quizzes_participants'

    id = db.Column(db.Integer, primary_key=True)
    competition_quiz_id = db.Column(db.Integer, db.ForeignKey('competition_quizzes.id'), nullable=False)  # Relación con CompetitionQuizzes
    participant_id = db.Column(db.Integer, nullable=False)  # ID del participante (de otro sistema/microservicio)
    
    score = db.Column(db.Integer, nullable=True, default=0)  # Puntaje obtenido en el cuestionario
    score_competition = db.Column(db.Integer, nullable=True, default=0) # Puntaje para la competencia

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

    # Relación con CompetitionQuiz
    competition_quiz = db.relationship('CompetitionQuiz', back_populates='participants')

    __table_args__ = (
        db.UniqueConstraint('competition_quiz_id', 'participant_id', name='uq_competition_quiz_participant'),  # Evita inscripciones duplicadas
    )

    def __repr__(self):
        return f"<CompetitionQuizParticipants CompetitionQuiz {self.competition_quiz_id} - Participant {self.participant_id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "competition_quiz_id": self.competition_quiz_id,
            "participant_id": self.participant_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

from extensions import db
from sqlalchemy.orm import relationship
import datetime as dt

class CompetitionQuizParticipants(db.Model):
    """
    Tabla intermedia para asociar los participantes a un quiz de una competencia.
    """
    __tablename__ = 'competition_quizzes_participants'

    id = db.Column(db.Integer, primary_key=True)
    competition_quiz_id = db.Column(db.Integer, db.ForeignKey('competition_quizzes.id'), nullable=False)  # Relación con CompetitionQuizzes
    participant_id = db.Column(db.Integer, nullable=False)  # ID del participante (de otro sistema/microservicio)
    
    start_time = db.Column(db.DateTime, nullable=True)  # Momento en el que el usuario inicia el cuestionario
    end_time = db.Column(db.DateTime, nullable=True)  # Momento en el que el usuario finaliza el cuestionario

    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

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

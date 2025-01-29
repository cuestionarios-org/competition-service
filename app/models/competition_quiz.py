from extensions import db
from sqlalchemy.orm import relationship
import datetime as dt

class CompetitionQuiz(db.Model):
    """
    Tabla intermedia para asociar competencias con los IDs de quizzes.
    """
    __tablename__ = 'competition_quizzes'

    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)  # Relación con Competitions
    quiz_id = db.Column(db.Integer, nullable=False)  # ID del quiz
    
    start_time = db.Column(db.DateTime, nullable=False, default=db.func.now())  # Inicio del cuestionario en la competencia
    end_time = db.Column(db.DateTime, nullable=False, default=db.func.now())  # Fin del cuestionario en la competencia

    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Relación con Competition
    competition = db.relationship('Competition', back_populates='quizzes')
    # Relación con CompetitionQuizParticipants
    participants = db.relationship('CompetitionQuizParticipants', back_populates='competition_quiz')
    
    __table_args__ = (
        db.UniqueConstraint('competition_id', 'quiz_id', name='uq_competition_quiz'),  # Evita duplicados
    )

    def __repr__(self):
        return f"<CompetitionQuiz Competition {self.competition_id} - Quiz {self.quiz_id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "competition_id": self.competition_id,
            "quiz_id": self.quiz_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

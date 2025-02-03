from extensions import db
from datetime import datetime, timezone
from app.utils.lib.formatting import safe_date_isoformat


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

    def __repr__(self):
        return f"<CompetitionQuiz Competition {self.competition_id} - Quiz {self.quiz_id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "competition_id": self.competition_id,
            "quiz_id": self.quiz_id,
            "time_limit": self.time_limit,
            "start_time": safe_date_isoformat(self.start_time),
            "end_time": safe_date_isoformat(self.end_time),
            "created_at": safe_date_isoformat(self.created_at),
            "updated_at": safe_date_isoformat(self.updated_at),
        }

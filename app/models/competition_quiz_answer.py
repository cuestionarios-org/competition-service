from extensions import db
from datetime import datetime, timezone

class CompetitionQuizAnswer(db.Model):
    __tablename__ = 'competition_quiz_answers'

    id = db.Column(db.Integer, primary_key=True)
    competition_quiz_id = db.Column(
        db.Integer, 
        db.ForeignKey('competition_quizzes.id'),  # Relación directa con el quiz de la competencia
        nullable=False
    )
    participant_id = db.Column(db.Integer, nullable=False)  # ID del participante (desde otro MS)
    answer_id = db.Column(db.Integer, nullable=False)  # ID de la respuesta del MS de quizzes

    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    question_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relación opcional para acceder al quiz (si es necesario)
    competition_quiz = db.relationship('CompetitionQuiz', back_populates='answers')

    __table_args__ = (
        db.UniqueConstraint(
            'competition_quiz_id', 
            'participant_id', 
            'answer_id', 
            name='uq_quiz_participant_answer'
        ),  # Evita respuestas duplicadas a la misma pregunta
        db.Index('idx_quiz_participant', 'competition_quiz_id', 'participant_id'),  # Búsquedas rápidas
    )

    def __repr__(self):
        return f"<CompetitionQuizAnswer Quiz {self.competition_quiz_id} - Participante {self.participant_id} - Respuesta {self.answer_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "competition_quiz_id": self.competition_quiz_id,
            "participant_id": self.participant_id,
            "answer_id": self.answer_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
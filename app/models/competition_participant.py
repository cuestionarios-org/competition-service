from extensions import db
from datetime import datetime, timezone

class CompetitionParticipant(db.Model):
    """
    Participantes inscritos en una competencia.
    """
    __tablename__ = 'competition_participants'

    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)  # Relación con Competitions
    participant_id = db.Column(db.Integer, nullable=False)  # ID del participante (de otro sistema/microservicio)

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

    competition = db.relationship('Competition', back_populates='participants')

    __table_args__ = (
        db.UniqueConstraint('competition_id', 'participant_id', name='uq_competition_participant'),  # Evita duplicados
    )

    def __repr__(self):
        return f"<CompetitionParticipant Competition {self.competition_id} - Participant {self.participant_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "competition_id": self.competition_id,
            "participant_id": self.participant_id,
            }
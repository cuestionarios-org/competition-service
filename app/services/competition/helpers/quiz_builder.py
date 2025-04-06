from dateutil import parser
from datetime import timezone
from .quiz_validator import validate_quiz_constraints
from app.models import CompetitionQuiz

def build_quiz_entry(competition, quiz_data, existing_quiz=None):
    if 'quiz_id' not in quiz_data:
        raise ValueError("Falta quiz_id en los datos del cuestionario.")

    start_time = parser.isoparse(quiz_data['start_time']) if quiz_data.get('start_time') else None
    end_time = parser.isoparse(quiz_data['end_time']) if quiz_data.get('end_time') else None

    if start_time and start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time and end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    validate_quiz_constraints(
        competition,
        quiz_data['quiz_id'],
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

from .quiz_builder import build_quiz_entry
from .quiz_validator import validate_quiz_constraints
from extensions import db

def update_quizzes(competition, incoming_quizzes_data):
    existing_quizzes = {q.quiz_id: q for q in competition.quizzes}
    incoming_quiz_ids = {q['quiz_id'] for q in incoming_quizzes_data}
    existing_quiz_ids = set(existing_quizzes.keys())

    _add_new_quizzes(competition, incoming_quizzes_data, existing_quiz_ids)
    _update_existing_quizzes(competition, incoming_quizzes_data, existing_quizzes)
    _remove_deleted_quizzes(competition, existing_quizzes, incoming_quiz_ids)

def _add_new_quizzes(competition, incoming_quizzes_data, existing_quiz_ids):
    for quiz_data in incoming_quizzes_data:
        if quiz_data['quiz_id'] not in existing_quiz_ids:
            quiz = build_quiz_entry(competition, quiz_data)
            db.session.add(quiz)

def _update_existing_quizzes(competition, incoming_quizzes_data, existing_quizzes):
    for quiz_data in incoming_quizzes_data:
        quiz_id = quiz_data['quiz_id']
        if quiz_id in existing_quizzes and {'start_time', 'end_time', 'time_limit'} & quiz_data.keys():
            existing_quiz = existing_quizzes[quiz_id]
            build_quiz_entry(competition, quiz_data, existing_quiz)

def _remove_deleted_quizzes(competition, existing_quizzes, incoming_quiz_ids):
    for quiz_id, quiz in existing_quizzes.items():
        if quiz_id not in incoming_quiz_ids:
            validate_quiz_constraints(
                competition,
                quiz_id=quiz.quiz_id,
                existing_start_time=quiz.start_time,
                is_removal=True
            )
            db.session.delete(quiz)

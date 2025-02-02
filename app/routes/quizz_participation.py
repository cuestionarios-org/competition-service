from flask import Blueprint, request, jsonify
from app.services.competition_quiz_participant_service import CompetitionQuizParticipantService
from werkzeug.exceptions import BadRequest, NotFound

quiz_participation_bp = Blueprint('quiz', __name__)

@quiz_participation_bp.route('/<int:competition_quiz_id>/participant/<int:participant_id>/start', methods=['POST'])
def start_quiz(competition_quiz_id, participant_id):
    try:
        participant = CompetitionQuizParticipantService.start_quiz(competition_quiz_id, participant_id)
        return jsonify(participant), 200
    except (BadRequest, NotFound) as e:
        return jsonify({"error": str(e)}), e.code if hasattr(e, 'code') else 400

@quiz_participation_bp.route('/<int:competition_quiz_id>/participant/<int:participant_id>/finish', methods=['POST'])
def finish_quiz(competition_quiz_id, participant_id):
    """
    en el json de la peticion se espera un objeto con la siguiente estructura:
    {
        "answers": [
            {
                "question_id": 1,
                "answer_id": 1
            },
            {
                "question_id": 2,
                "answer_id": 2
    """
    data = request.get_json(silent=True)
    if not data or 'answers' not in data:
        return jsonify({"error": "Missing answers in request body"}), 400
    if not data or 'quiz' not in data:
        return jsonify({"error": "Missing data quiz in request body"}), 400
    
    try:
        result = CompetitionQuizParticipantService.finish_quiz(
            competition_quiz_id=competition_quiz_id,
            participant_id=participant_id,
            answers=data['answers'],
            quiz=data['quiz']
        )
        return jsonify(result), 200
    except (BadRequest, NotFound) as e:
        return jsonify({"error": str(e)}), e.code if hasattr(e, 'code') else 400

@quiz_participation_bp.route('/<int:competition_quiz_id>/participant/<int:participant_id>/answers', methods=['GET'])
def get_user_quiz_answers(competition_quiz_id, participant_id):
    try:
        answers = CompetitionQuizParticipantService.get_by_user_and_quiz(
            competition_quiz_id=competition_quiz_id,
            participant_id=participant_id
        )
        return jsonify(answers), 200
    except (BadRequest, NotFound) as e:
        return jsonify({"error": str(e)}), e.code if hasattr(e, 'code') else 400

@quiz_participation_bp.route('/<int:competition_quiz_id>/answers', methods=['GET'])
def get_all_quiz_answers(competition_quiz_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    try:
        result = CompetitionQuizParticipantService.get_all_for_quiz(
            competition_quiz_id=competition_quiz_id,
            page=page,
            per_page=per_page
        )
        return jsonify(result), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404

@quiz_participation_bp.route('/<int:competition_quiz_id>/participant/<int:participant_id>', methods=['GET'])
def get_complete_quiz_by_user(competition_quiz_id, participant_id):
    try:
        participant = CompetitionQuizParticipantService.get_complete_quiz_by_user(
            competition_quiz_id=competition_quiz_id,
            participant_id=participant_id
        )
        return jsonify(participant), 200
    except (BadRequest, NotFound) as e:
        return jsonify({"error": str(e)}), e.code if hasattr(e, 'code') else 400
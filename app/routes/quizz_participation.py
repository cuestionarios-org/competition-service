from flask import Blueprint, request, jsonify
from app.services.competition_quiz_participant_service import CompetitionQuizParticipantService

quiz_participation_bp = Blueprint('quiz', __name__)

@quiz_participation_bp.route('/<int:competition_quiz_id>/participant/<int:participant_id>/start', methods=['POST'])
def start_quiz(competition_quiz_id, participant_id):
    print(">>>>>>>>>>",competition_quiz_id, participant_id)
    participant = CompetitionQuizParticipantService.start_quiz(competition_quiz_id, participant_id)
    return jsonify(participant), 200

@quiz_participation_bp.route('/<int:competition_quiz_id>/participant/<int:participant_id>/finish', methods=['POST'])
def finish_quiz(competition_quiz_id, participant_id):
    participant = CompetitionQuizParticipantService.finish_quiz(competition_quiz_id, participant_id)
    return jsonify(participant), 200

@quiz_participation_bp.route('/<int:competition_quiz_id>/participant/<int:participant_id>', methods=['GET'])
def get_complete_quiz_by_user(competition_quiz_id, participant_id):
    participant = CompetitionQuizParticipantService.get_complete_quiz_by_user(competition_quiz_id, participant_id)
    return jsonify(participant), 200

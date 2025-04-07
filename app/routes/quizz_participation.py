from flask import Blueprint, request, jsonify
from app.services import CompetitionQuizParticipantService
from werkzeug.exceptions import BadRequest, NotFound

# 📦 Blueprint para rutas relacionadas con la participación en quizzes dentro de competencias
quiz_participation_bp = Blueprint('quiz', __name__)

# -------------------------------------------------------
# 🟢 Iniciar un quiz para un participante específico
# POST /<competition_quiz_id>/participant/<participant_id>/start
# -------------------------------------------------------
@quiz_participation_bp.route('/<int:competition_quiz_id>/participant/<int:participant_id>/start', methods=['POST'])
def start_quiz(competition_quiz_id, participant_id):
    """
    Inicia el quiz de una competencia para un participante.
    """
    try:
        participant = CompetitionQuizParticipantService.start_quiz(competition_quiz_id, participant_id)
        return jsonify(participant), 200
    except (BadRequest, NotFound) as e:
        return jsonify({"error": str(e)}), e.code if hasattr(e, 'code') else 400

# -------------------------------------------------------
# 🟣 Finalizar un quiz con respuestas
# POST /<competition_quiz_id>/participant/<participant_id>/finish
# -------------------------------------------------------
@quiz_participation_bp.route('/<int:competition_quiz_id>/participant/<int:participant_id>/finish', methods=['POST'])
def finish_quiz(competition_quiz_id, participant_id):
    """
    Finaliza el quiz de una competencia para un participante.
    
    El cuerpo de la solicitud debe incluir un JSON con la siguiente estructura:
    {
        "answers": [
            {
                "question_id": 1,
                "answer_id": 1
            },
            {
                "question_id": 2,
                "answer_id": 2
            }
        ]
    }
    """
    data = request.get_json(silent=True)
    if not data or 'answers' not in data:
        return jsonify({"error": "Missing answers in request body"}), 400
    
    try:
        result = CompetitionQuizParticipantService.finish_quiz(
            competition_quiz_id=competition_quiz_id,
            participant_id=participant_id,
            answers=data['answers']
        )
        return jsonify(result), 200
    except (BadRequest, NotFound) as e:
        return jsonify({"error": str(e)}), e.code if hasattr(e, 'code') else 400

# -------------------------------------------------------
# 🔍 Obtener respuestas de un participante específico
# GET /<competition_quiz_id>/participant/<participant_id>/answers
# -------------------------------------------------------
@quiz_participation_bp.route('/<int:competition_quiz_id>/participant/<int:participant_id>/answers', methods=['GET'])
def get_user_quiz_answers(competition_quiz_id, participant_id):
    """
    Devuelve las respuestas enviadas por un participante en un quiz.
    """
    try:
        answers = CompetitionQuizParticipantService.get_by_user_and_quiz(
            competition_quiz_id=competition_quiz_id,
            participant_id=participant_id
        )
        return jsonify(answers), 200
    except (BadRequest, NotFound) as e:
        return jsonify({"error": str(e)}), e.code if hasattr(e, 'code') else 400

# -------------------------------------------------------
# 📋 Obtener todas las respuestas del quiz (paginado)
# GET /<competition_quiz_id>/answers?page=1&per_page=50
# -------------------------------------------------------
@quiz_participation_bp.route('/<int:competition_quiz_id>/answers', methods=['GET'])
def get_all_quiz_answers(competition_quiz_id):
    """
    Devuelve todas las respuestas enviadas en un quiz específico (soporta paginación).

    Parámetros opcionales:
    - page: número de página (por defecto 1)
    - per_page: cantidad de respuestas por página (por defecto 50)
    """
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

# -------------------------------------------------------
# 📚 Obtener detalle completo del quiz respondido por un usuario
# GET /<competition_quiz_id>/participant/<participant_id>
# -------------------------------------------------------
@quiz_participation_bp.route('/<int:competition_quiz_id>/participant/<int:participant_id>', methods=['GET'])
def get_complete_quiz_by_user(competition_quiz_id, participant_id):
    """
    Devuelve todo el detalle del quiz resuelto por un participante,
    incluyendo preguntas, respuestas seleccionadas y resultado final.
    """
    try:
        participant = CompetitionQuizParticipantService.get_complete_quiz_by_user(
            competition_quiz_id=competition_quiz_id,
            participant_id=participant_id
        )
        return jsonify(participant), 200
    except (BadRequest, NotFound) as e:
        return jsonify({"error": str(e)}), e.code if hasattr(e, 'code') else 400

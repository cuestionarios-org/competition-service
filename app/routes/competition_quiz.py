from flask import Blueprint, request, jsonify
from app.models import CompetitionQuiz
from app.services.competition_quiz import CompetitionQuizService
from werkzeug.exceptions import NotFound, BadRequest

competition_quiz_bp = Blueprint('competition_quiz', __name__)

@competition_quiz_bp.route('', methods=['GET'])
def list_competition_quizzes():
    print("🔎 xxxxxxGET /competition-quiz llamado")
    quizzes = CompetitionQuiz.query.all()
    quizzes_list = [q.to_dict() for q in quizzes]
    print(f"🔎 Se encontraron {len(quizzes_list)} CompetitionQuiz")
    return jsonify({"quizzes": quizzes_list}), 200

@competition_quiz_bp.route('/<int:competition_quiz_id>', methods=['PATCH'])
def update_competition_quiz(competition_quiz_id):
    """
    Actualiza los campos start_time, end_time y time_limit de un CompetitionQuiz.
    Request JSON esperado: { "start_time": ..., "end_time": ..., "time_limit": ... }
    """
    print(f"XXXXXXXXXXX PUT /competition-quiz/{competition_quiz_id} llamado")
    data = request.get_json()
    if not data:
        print("❌ No se recibieron datos JSON válidos")
        return jsonify({"msg": "Datos inválidos."}), 400
    try:
        print(f"🔄 Actualizando CompetitionQuiz con ID {competition_quiz_id}...")
        updated_quiz = CompetitionQuizService.update_competition_quiz(competition_quiz_id, data)
        print(f"✅ CompetitionQuiz actualizado: {updated_quiz.to_dict()}")
        return jsonify({"msg": "CompetitionQuiz actualizado correctamente.", "quiz": updated_quiz.to_dict()}), 200
    except (NotFound, BadRequest) as e:
        print(f"❌ Error esperado: {str(e)}")
        return jsonify({"msg": str(e)}), 400
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return jsonify({"msg": f"Error inesperado: {str(e)}"}), 500

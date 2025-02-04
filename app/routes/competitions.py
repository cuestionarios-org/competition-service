from flask import Blueprint, request, jsonify
from app.services import CompetitionService, CompetitionParticipantService

# Blueprint para las rutas de Competition
competition_bp = Blueprint('competition', __name__)

# Ruta para crear una nueva competencia
@competition_bp.route('/', methods=['POST'])
def create_competition():
    """
    Crea una nueva competencia.
    """
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Invalid data."}), 400

    try:
        competition = CompetitionService.create_competition(data)
        return jsonify({"msg": "Competition created successfully.", "competition": competition.to_dict()}), 201
    except Exception as e:
        return jsonify({"msg": "An error occurred.", "error": str(e)}), 500

# Ruta para obtener todas las competencias
@competition_bp.route('/', methods=['GET'])
def get_all_competitions():
    """
    Lista todas las competencias.
    """
    try:
        competitions = CompetitionService.get_all_competitions()
        result = [competition.to_dict() for competition in competitions]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"msg": "An error occurred.", "error": str(e)}), 500

# Ruta para obtener una competencia por ID
@competition_bp.route('/<int:id>', methods=['GET'])
def get_competition_by_id(id):
    """
    Obtiene una competencia por su ID.
    """
    try:
        competition = CompetitionService.get_competition(id)
        return jsonify(competition.to_dict()), 200
    except Exception as e:
        return jsonify({"msg": f"Error fetching competition: {str(e)}"}), 400

# Ruta para actualizar una competencia por ID
@competition_bp.route('/<int:id>', methods=['PUT'])
def update_competition(id):
    """
    Actualiza una competencia por su ID.
    """
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Invalid data."}), 400

    try:
        updated_competition = CompetitionService.update_competition(id, data)
        return jsonify({"msg": "Competition updated successfully.", "competition": updated_competition.to_dict()}), 200
    except Exception as e:
        return jsonify({"msg": f"Error updating competition: {str(e)}"}), 400

# Ruta para eliminar una competencia por ID
@competition_bp.route('/<int:id>', methods=['DELETE'])
def delete_competition(id):
    """
    Elimina una competencia por su ID.
    """
    try:
        CompetitionService.delete_competition(id)
        return jsonify({"msg": "Competition deleted successfully."}), 200
    except Exception as e:
        return jsonify({"msg": f"Error deleting competition: {str(e)}"}), 400



# Ruta para inscribir un participante en una competencia
@competition_bp.route('/<int:competition_id>/participants/<int:participant_id>', methods=['POST'])
def add_participant_to_competition(competition_id, participant_id):
    """
    Inscribe un participante en una competencia.
    """
    try:
        participant = CompetitionParticipantService.add_participant_to_competition(competition_id, participant_id)
        return jsonify({"msg": "Participant added to competition successfully.", "participant": participant.to_dict()}), 201
    except Exception as e:
        return jsonify({"msg": f"Error adding participant to competition: {str(e)}"}), 400

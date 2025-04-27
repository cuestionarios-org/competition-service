# Importaciones necesarias
from flask import Blueprint, request, jsonify
from app.services import CompetitionService, CompetitionParticipantService

# Blueprint para agrupar las rutas relacionadas con "Competition"
competition_bp = Blueprint('competition', __name__)

# --------------------------------------------
# 📌 Ruta: Crear una nueva competencia
# --------------------------------------------

@competition_bp.route('/', methods=['POST'])
def create_competition():
    """
    Crea una nueva competencia.

    Método: POST
    Endpoint: /competitions/

    Request JSON esperado:
    {
        "title": "Nombre de la competencia",
        "start_date": "YYYY-MM-DDTHH:MM:SSZ",
        "end_date": "YYYY-MM-DDTHH:MM:SSZ",
        "created_by": "usuario123",
        ...
    }

    Respuestas:
    - 201: Competencia creada exitosamente
    - 400: Datos inválidos
    - 500: Error interno del servidor
    """
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Invalid data."}), 400

    try:
        competition = CompetitionService.create_competition(data)
        return jsonify({
            "msg": "Competition created successfully.",
            "competition": competition.to_dict()
        }), 201
    except Exception as e:
        return jsonify({"msg": "An error occurred.", "error": str(e)}), 500

# --------------------------------------------
# 📌 Ruta: Obtener todas las competencias
# --------------------------------------------
@competition_bp.route('/', methods=['GET'])
def get_all_competitions():
    """
    Lista todas las competencias existentes.

    Método: GET
    Endpoint: /competitions/

    Respuestas:
    - 200: Lista de competencias
    - 500: Error al obtener los datos
    """
    try:
        competitions = CompetitionService.get_all_competitions()
        result = [competition.to_dict() for competition in competitions]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"msg": "An error occurred.", "error": str(e)}), 500

# --------------------------------------------
# 📌 Ruta: Obtener competencia por ID
# --------------------------------------------
@competition_bp.route('/<int:id>', methods=['GET'])
def get_competition_by_id(id):
    """
    Obtiene una competencia específica por su ID.

    Método: GET
    Endpoint: /competitions/<id>

    Respuestas:
    - 200: Competencia encontrada
    - 400: Error al buscar la competencia
    """
    try:
        competition = CompetitionService.get_competition(id)
        return jsonify(competition.to_dict()), 200
    except Exception as e:
        return jsonify({"msg": f"Error fetching competition: {str(e)}"}), 400

# --------------------------------------------
# 📌 Ruta: Actualizar competencia por ID
# --------------------------------------------
@competition_bp.route('/<int:id>', methods=['PUT']) 
def update_competition(id):
    """
    Actualiza los datos de una competencia existente.

    Método: PUT
    Endpoint: /competitions/<id>

    Request JSON esperado: datos parciales o completos de la competencia.

    Respuestas:
    - 200: Competencia actualizada exitosamente
    - 400: Datos inválidos o error en la actualización
    """
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Invalid data."}), 400

    try:
        updated_competition = CompetitionService.update_competition(id, data)
        return jsonify({
            "msg": "Competition updated successfully.",
            "competition": updated_competition.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"msg": f"Error updating competition: {str(e)}"}), 400

# --------------------------------------------
# 📌 Ruta: Eliminar competencia por ID
# --------------------------------------------
@competition_bp.route('/<int:id>', methods=['DELETE'])
def delete_competition(id):
    """
    Elimina una competencia por su ID.

    Método: DELETE
    Endpoint: /competitions/<id>

    Respuestas:
    - 200: Competencia eliminada
    - 400: Error al intentar eliminar
    """
    try:
        CompetitionService.delete_competition(id)
        return jsonify({"msg": "Competition deleted successfully."}), 200
    except Exception as e:
        return jsonify({"msg": f"Error deleting competition: {str(e)}"}), 400

# --------------------------------------------
# 📌 Ruta: Inscribir participante en una competencia
# --------------------------------------------
@competition_bp.route('/<int:competition_id>/participants/<int:participant_id>', methods=['POST'])
def add_participant_to_competition(competition_id, participant_id):
    """
    Inscribe un participante en una competencia.

    Método: POST
    Endpoint: /competitions/<competition_id>/participants/<participant_id>

    Respuestas:
    - 201: Participante inscrito exitosamente
    - 400: Error en la inscripción
    """
    try:
        participant = CompetitionParticipantService.add_participant_to_competition(competition_id, participant_id)
        return jsonify({
            "msg": "Participant added to competition successfully.",
            "participant": participant.to_dict()
        }), 201
    except Exception as e:
        return jsonify({"msg": f"Error adding participant to competition: {str(e)}"}), 400

# --------------------------------------------
# 📌 Ruta: Obtener ranking de una competencia
# --------------------------------------------
@competition_bp.route('/<int:competition_id>/ranking', methods=['GET'])
def get_competition_ranking(competition_id):
    """
    Obtiene el ranking (posiciones) de los participantes en una competencia.

    Método: GET
    Endpoint: /competitions/<competition_id>/ranking

    Respuestas:
    - 200: Lista ordenada de participantes con sus puntajes
    - 400: Error al generar el ranking
    """
    try:
        ranking = CompetitionParticipantService.get_competition_ranking_with_quizzes_computables(competition_id)
        return jsonify(ranking), 200
    except Exception as e:
        return jsonify({"msg": f"Error fetching competition ranking: {str(e)}"}), 400

# --------------------------------------------
# 📚 Ruta: Obtener competencias de un usuario
# --------------------------------------------
@competition_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_competitions(user_id):
    """
    Obtiene las competencias relacionadas con un usuario:
      - pending: aún no inscritas (start_date > ahora)
      - active: en curso y donde participa
      - finished: finalizadas y donde participó

    Método: GET
    Endpoint: /competitions/users/<user_id>
    Query params opcionales:
      - status: 'pending', 'active', 'finished' (separados por comas)
        p.ej. ?status=active,finished
    Respuestas:
      - 200: { "pending": [...], "active": [...], "finished": [...] }
      - 400: parámetro inválido
      - 500: error interno
    """
    try:
        # Extraigo el parámetro `status`, si existe
        status_param = request.args.get('status')
        statuses = status_param.split(',') if status_param else None

        # Delego a un servicio que implemente la lógica
        # Deberías crear CompetitionService.get_user_competitions
        result = CompetitionParticipantService.get_user_competitions(user_id, statuses)

        # Espero que `result` sea algo como:
        # { "pending": [...], "active": [...], "finished": [...] }
        return jsonify(result), 200

    except ValueError as ve:
        # Por ejemplo, estado inválido
        return jsonify({ "msg": str(ve) }), 400

    except Exception as e:
        return jsonify({
            "msg": "Error al obtener competencias del usuario",
            "error": str(e)
        }), 500

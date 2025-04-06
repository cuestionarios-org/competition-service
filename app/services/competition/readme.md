# 🏆 Servicio de Competencias

Este servicio permite administrar competencias y sus quizzes asociados.

## Endpoints principales

| Método | Ruta              | Descripción                        |
|--------|-------------------|------------------------------------|
| GET    | /competitions     | Listar todas las competencias     |
| POST   | /competitions     | Crear una competencia             |
| GET    | /competitions/:id | Obtener competencia por ID        |
| PUT    | /competitions/:id | Actualizar competencia (quizzes)  |

## Ejemplo de payload (POST /competitions)

```json
{
  "title": "Trivia Mundial 2025",
  "description": "Competencia para todos",
  "start_date": "2025-05-01T00:00:00Z",
  "end_date": "2025-05-31T23:59:59Z",
  "created_by": "admin",
  "participant_limit": 100,
  "currency_cost": 200,
  "quizzes": [
    {
      "quiz_id": 1,
      "order": 1,
      "points": 100
    }
  ]
}

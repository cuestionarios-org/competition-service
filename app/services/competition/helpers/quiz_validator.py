from datetime import datetime, timezone

def validate_quiz_constraints(
    competition, quiz_id,
    start_time=None, end_time=None,
    existing_start_time=None,
    is_modifying=False,
    is_removal=False
):
    now = datetime.now(timezone.utc)

    competition_start = competition.start_date.astimezone(timezone.utc)
    competition_end = competition.end_date.astimezone(timezone.utc)

    if is_removal and competition.state not in {'preparacion', 'lista'}:
        raise ValueError(f"No se puede eliminar quizzes en estado '{competition.state}'.")
    
    if is_modifying and competition.state not in {'preparacion', 'lista', 'en curso'}:
        raise ValueError(f"No se pueden modificar quizzes cuando la competencia tiene estado '{competition.state}'.")
    
    if not is_removal and not is_modifying and competition.state not in {'preparacion', 'lista', 'en curso'}:
        raise ValueError(f"No se pueden agregar quizzes en estado '{competition.state}'.")

    if existing_start_time and existing_start_time <= now:
        if is_modifying:
            raise ValueError(f"No se puede modificar el quiz '{quiz_id}' porque ya ha comenzado.")
        if is_removal:
            raise ValueError(f"No se puede eliminar el quiz '{quiz_id}' porque ya ha comenzado.")

    if start_time and start_time <= now and is_modifying:
        raise ValueError(f"No se puede asignar una fecha de inicio en el pasado ({quiz_id}).")

    if start_time and start_time < competition_start:
        raise ValueError("La fecha de inicio del quiz no puede ser anterior a la de la competencia.")

    if end_time and end_time > competition_end:
        raise ValueError("La fecha de fin del quiz no puede ser posterior a la de la competencia.")

    if start_time and end_time and start_time > end_time:
        raise ValueError("La fecha de inicio no puede ser posterior a la de fin.")

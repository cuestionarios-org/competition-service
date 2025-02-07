from datetime import datetime
from dateutil import parser

def safe_date_isoformat(date):
    """
    Convierte fechas a ISO 8601 manejando todos los casos posibles
    """
    if isinstance(date, datetime):
        return date.isoformat()
    elif isinstance(date, str):  # Para datos legacy o entradas incorrectas
        try:
            parsed_date = parser.isoparse(date)
            return parsed_date.isoformat()
        except (ValueError, TypeError):
            return None
    return None  # Para None u otros tipos
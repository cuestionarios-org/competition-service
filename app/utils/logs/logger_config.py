import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Configura el logger para registrar errores en un archivo con rotación.
    """
    # Configura un handler con rotación de archivos
    handler = RotatingFileHandler(
        'errors.log',  # Nombre del archivo de log
        maxBytes=100000,  # Tamaño máximo del archivo en bytes (100 KB)
        backupCount=5     # Número de backups antes de sobrescribir
    )
    handler.setLevel(logging.ERROR)  # Nivel de log (solo errores y más graves)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # Configura el logger principal
    logger = logging.getLogger()  # Obtén el logger raíz
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)  # Nivel de log para la aplicación

class CustomException(Exception):
    """
    Excepción personalizada para manejar errores en la aplicación.

    Args:
        message (str): Mensaje descriptivo del error.
        code (int, opcional): Código de error personalizado. Por defecto es 500 (error genérico).
        log_error (bool, opcional): Si es True, el error será registrado automáticamente en el log.
    """
    def __init__(self, message, code=500, log_error=True):
        super().__init__(message)
        self.message = message
        self.code = code

        if log_error:
            self.log_error()

    def log_error(self):
        """
        Registra el error en el sistema de logs.
        Este método se puede personalizar para integrar con herramientas externas de monitoreo o logs.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error [{self.code}]: {self.message}")

    def to_dict(self):
        """
        Convierte los detalles de la excepción a un diccionario.

        Returns:
            dict: Diccionario con el mensaje de error y el código de error.
        """
        return {"error": self.message, "code": self.code}

class ValidationError(CustomException):
    def __init__(self, message="Datos de entrada no válidos", code=400):
        super().__init__(message, code)


class AuthorizationError(CustomException):
    def __init__(self, message="No tienes permisos para realizar esta acción", code=403):
        super().__init__(message, code)

class PermissionError(CustomException):
    """
    Error relacionado con permisos.
    """
    def __init__(self, message, code=403):
        super().__init__(message, code)
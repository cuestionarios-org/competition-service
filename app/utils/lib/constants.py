class CompetitionQuizStatus:
    ACTIVO = "ACTIVO"
    COMPUTABLE = "COMPUTABLE"
    NO_COMPUTABLE = "NO_COMPUTABLE"

    @classmethod
    def values(cls):
        """Devuelve un conjunto con los valores permitidos."""
        return {cls.ACTIVO, cls.COMPUTABLE, cls.NO_COMPUTABLE}

    @classmethod
    def has_value(cls, value):
        """Verifica si el valor existe en la lista de estados válidos."""
        return value in cls.values()

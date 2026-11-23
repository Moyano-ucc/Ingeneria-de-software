class NivoraError(Exception):
    """Base para errores controlados de la aplicación."""


class ResourceNotFoundError(NivoraError):
    pass


class LessonLockedError(NivoraError):
    pass

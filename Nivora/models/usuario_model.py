from services.auth_service import AuthService


class UsuarioModel:
    """Compatibility facade for callers that still use the old model API."""

    _service = AuthService()

    @classmethod
    def registrar(cls, nombre, email, password):
        return cls._service.register(nombre, email, password)

    @classmethod
    def autenticar(cls, email, password):
        return cls._service.authenticate(email, password)
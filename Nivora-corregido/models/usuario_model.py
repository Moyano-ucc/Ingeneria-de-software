class UsuarioModel:
    # Simulación de una base de datos en memoria
    usuarios_db = []

    @classmethod
    def registrar(cls, email, password):
        # Verifica si el correo ya está registrado
        for usuario in cls.usuarios_db:
            if usuario['email'] == email:
                return False, "El correo electrónico ya está registrado"

        cls.usuarios_db.append({
            "email": email,
            "password": password
        })

        return True, "Cuenta creada exitosamente"

    @classmethod
    def autenticar(cls, email, password):
        # Verifica que las credenciales coincidan
        for usuario in cls.usuarios_db:
            if usuario['email'] == email and usuario['password'] == password:
                return True

        return False
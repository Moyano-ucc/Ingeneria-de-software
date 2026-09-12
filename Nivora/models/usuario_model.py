class UsuarioModel:
    # Simulación de base de datos en memoria
    usuarios_db = []

    @classmethod
    def registrar(cls, email, password):
        # Comprueba si el correo ya existe (Scenario: Registro con correo existente)[cite: 1]
        for user in cls.usuarios_db:
            if user['email'] == email:
                return False, "El correo electrónico ya está registrado"
        
        cls.usuarios_db.append({"email": email, "password": password})
        return True, "Cuenta creada exitosamente"

    @classmethod
    def autenticar(cls, email, password):
        # Valida credenciales (Scenario: Inicio de sesión exitoso)[cite: 1]
        for user in cls.usuarios_db:
            if user['email'] == email and user['password'] == password:
                return True
        return False
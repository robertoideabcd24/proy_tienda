from extension import pgdb

class UsuarioException(Exception): pass

class Usuario:
    def __init__(self, nombre=None, fecha_nacimiento=None, rol=None, correo=None, contrasena=None):
        self.nombre = nombre
        self.fecha_nacimiento = fecha_nacimiento
        self.rol = rol
        self.correo = correo
        self.contrasena = contrasena

    @property
    def db(self):
        global pgdb
        if pgdb is None:
            raise UsuarioException("La conexión a la base de datos no ha sido inicializada")
        return pgdb

    @staticmethod
    def verificar_usuario(nombre, contrasena):
        try:
            if not nombre or not contrasena:
                raise UsuarioException("Nombre de usuario y contraseña son obligatorios.")
            
            with pgdb.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, nombre_usuario, correo, rol FROM usuarios WHERE nombre_usuario = %s AND contrasena = %s",
                    (nombre, contrasena)
                )
                resultado = cursor.fetchone()

            if resultado:
                return {
                    'id': resultado[0],
                    'nombre': resultado[1],
                    'correo': resultado[2],
                    'rol': resultado[3]
                }
            else:
                return None  # credenciales incorrectas

        except Exception as e:
            raise UsuarioException(f"Error al verificar usuario: {e}")


    @staticmethod
    def insertar_usuario_en_db(nombre, fecha_nacimiento, rol, correo, contrasena):
        try:
            if not all([nombre, fecha_nacimiento, rol, correo, contrasena]):
                raise UsuarioException("Todos los campos son obligatorios para registrar un usuario.")
            
            with pgdb.get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO usuarios (nombre_usuario, fecha_nacimiento, rol, correo, contrasena)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (nombre, fecha_nacimiento, rol, correo, contrasena)
                )
                cursor.connection.commit()
            return True

        except Exception as e:
            raise UsuarioException(f"Error al insertar usuario: {e}")
#cerrar sesion
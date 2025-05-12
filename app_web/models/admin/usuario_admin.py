from ...extension import pgdb

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
            with pgdb.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, nombre_usuario, correo, rol FROM usuarios WHERE nombre_usuario = %s AND contrasena = %s",
                    (nombre, contrasena)
                )
                resultado = cursor.fetchone()
            if resultado:
                return {
                    'id': resultado[0],         # id del usuario
                    'nombre': resultado[1],     # nombre del usuario
                    'correo': resultado[2],     # correo del usuario
                    'rol': resultado[3]         # rol del usuario
                }
        except Exception as e:
            print("Error al verificar usuario:", e)
        return None


    @staticmethod
    def insertar_usuario_en_db(nombre, fecha_nacimiento, rol, correo, contrasena):
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO usuarios (nombre_usuario, fecha_nacimiento, rol, correo, contrasena) VALUES (%s, %s, %s, %s, %s)",
                    (nombre, fecha_nacimiento, rol, correo, contrasena)
                )
                cursor.connection.commit()
            return True
        except Exception as e:
            print("Error al insertar usuario:", e)
            return False
#cerrar sesion
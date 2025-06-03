import pytest
from app_web.models.admin.usuario_admin import Usuario, UsuarioException
from app_web.extension import pgdb  


@pytest.fixture
def usuario_valido():
    return ("TestUser", "1990-01-01", "user", "test@example.com", "testpass123")


@pytest.mark.parametrize("nombre,fecha_nacimiento,rol,correo,contrasena,expected_error", [
   
    (None, "1995-08-10", "user", "ana@example.com", "securepass", "Todos los campos son obligatorios"),
    ("Ana", None, "user", "ana@example.com", "securepass", "Todos los campos son obligatorios"),
    ("", "1995-08-10", "user", "ana@example.com", "securepass", "Todos los campos son obligatorios"),
    ("Ana", "", "user", "ana@example.com", "securepass", "Todos los campos son obligatorios"),
    ("Ana", "invalid-date", "user", "ana@example.com", "securepass", "Formato de fecha inválido"),
])
def test_validaciones_insertar_usuario(nombre, fecha_nacimiento, rol, correo, contrasena, expected_error):
    if expected_error:
        with pytest.raises(UsuarioException) as excinfo:
            Usuario.insertar_usuario_en_db(nombre, fecha_nacimiento, rol, correo, contrasena)
        assert expected_error in str(excinfo.value)
    else:

        try:
            Usuario.insertar_usuario_en_db(nombre, fecha_nacimiento, rol, correo, contrasena)
        except UsuarioException:
            pytest.fail("Validación falló con datos correctos")



@pytest.mark.parametrize("username,password,expected_exception", [
    ("valid", "valid", None),
    ("", "valid", "Nombre de usuario y contraseña son obligatorios."),
    ("valid", "", "Nombre de usuario y contraseña son obligatorios."),
    (None, "valid", "Nombre de usuario y contraseña son obligatorios."),
    ("valid", None, "Nombre de usuario y contraseña son obligatorios."),
])
def test_verificar_usuario_validaciones(username, password, expected_exception):
    if expected_exception:
        with pytest.raises(UsuarioException) as excinfo:
            Usuario.verificar_usuario(username, password)
        assert expected_exception in str(excinfo.value)
    else:

        try:
            Usuario.verificar_usuario(username, password)
        except UsuarioException:
            pytest.fail("No debería lanzar excepción con datos válidos")


@pytest.mark.parametrize("nombre,fecha_nacimiento,rol,correo,contrasena,expected_exception", [
    ("Ana", "1995-08-10", "user", "ana@example.com", "securepass", None),
    (None, "1995-08-10", "user", "ana@example.com", "securepass", "Todos los campos son obligatorios"),
    ("Ana", None, "user", "ana@example.com", "securepass", "Todos los campos son obligatorios"),
    ("Ana", "1995-08-10", None, "ana@example.com", "securepass", "Todos los campos son obligatorios"),
    ("Ana", "1995-08-10", "user", None, "securepass", "Todos los campos son obligatorios"),
    ("Ana", "1995-08-10", "user", "ana@example.com", None, "Todos los campos son obligatorios"),
    ("", "1995-08-10", "user", "ana@example.com", "securepass", "Todos los campos son obligatorios"),
    ("Ana", "", "user", "ana@example.com", "securepass", "Todos los campos son obligatorios"),
    ("Ana", "1995-08-10", "", "ana@example.com", "securepass", "Todos los campos son obligatorios"),
    ("Ana", "1995-08-10", "user", "", "securepass", "Todos los campos son obligatorios"),
    ("Ana", "1995-08-10", "user", "ana@example.com", "", "Todos los campos son obligatorios"),
    ("Ana", "invalid-date", "user", "ana@example.com", "securepass", "Formato de fecha inválido"),
])



def test_usuario_constructor_validaciones(nombre, fecha_nacimiento, rol, correo, contrasena, expected_exception):
    if expected_exception:
        with pytest.raises(UsuarioException) as excinfo:
            Usuario(
                nombre=nombre,
                fecha_nacimiento=fecha_nacimiento,
                rol=rol,
                correo=correo,
                contrasena=contrasena
            )
        assert expected_exception in str(excinfo.value)
    else:
        usuario = Usuario(
            nombre=nombre,
            fecha_nacimiento=fecha_nacimiento,
            rol=rol,
            correo=correo,
            contrasena=contrasena
        )
        assert usuario.nombre == nombre
        assert usuario.fecha_nacimiento == fecha_nacimiento
        assert usuario.rol == rol
        assert usuario.correo == correo
        assert usuario.contrasena == contrasena
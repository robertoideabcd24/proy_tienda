import pytest
from unittest.mock import MagicMock
from app_web.models.admin.usuario_admin import Usuario, UsuarioException 
from app_web.extension import pgdb
from app_web import extension


@pytest.fixture
def mock_pgdb_cursor(mocker):
    mock_cursor = MagicMock()
    mocker.patch('app_web.extension.pgdb.get_cursor', return_value=mock_cursor)
    return mock_cursor


def test_verificar_usuario_exito(mock_pgdb_cursor):
    mock_cursor = MagicMock()
    mock_pgdb_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1, 'roberto', 'roberto@mail.com', 'admin')

    resultado = Usuario.verificar_usuario('roberto', '1234')

    assert resultado == {
        'id': 1,
        'nombre': 'roberto',
        'correo': 'roberto@mail.com',
        'rol': 'admin'
    }


def test_verificar_usuario_credenciales_incorrectas(mock_pgdb_cursor):
    mock_cursor = MagicMock()
    mock_pgdb_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    resultado = Usuario.verificar_usuario('invalido', 'mal')

    assert resultado is None


def test_verificar_usuario_sin_datos():
    with pytest.raises(UsuarioException) as excinfo:
        Usuario.verificar_usuario('', '')
    assert "Nombre de usuario y contraseña son obligatorios." in str(excinfo.value)


def test_verificar_usuario_error_db(mock_pgdb_cursor):
    mock_cursor = MagicMock()
    mock_pgdb_cursor.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("DB error")

    with pytest.raises(UsuarioException) as excinfo:
        Usuario.verificar_usuario('user', 'pass')
    assert "Error al verificar usuario" in str(excinfo.value)


def test_insertar_usuario_exito(mock_pgdb_cursor):
    mock_cursor = MagicMock()
    mock_pgdb_cursor.__enter__.return_value = mock_cursor
    mock_cursor.execute.return_value = None

    resultado = Usuario.insertar_usuario_en_db(
        nombre="Ana",
        fecha_nacimiento="1995-08-10",
        rol="user",
        correo="ana@example.com",
        contrasena="securepass"
    )
    assert resultado is True


def test_insertar_usuario_faltan_datos():
    with pytest.raises(UsuarioException) as excinfo:
        Usuario.insertar_usuario_en_db(
            nombre="Ana",
            fecha_nacimiento=None,
            rol="user",
            correo="ana@example.com",
            contrasena="securepass"
        )
    assert "Todos los campos son obligatorios" in str(excinfo.value)


def test_insertar_usuario_error_db(mock_pgdb_cursor):
    mock_cursor = MagicMock()
    mock_pgdb_cursor.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Error SQL")

    with pytest.raises(UsuarioException) as excinfo:
        Usuario.insertar_usuario_en_db(
            nombre="Luis",
            fecha_nacimiento="1990-01-01",
            rol="admin",
            correo="luis@example.com",
            contrasena="1234"
        )
    assert "Error al insertar usuario" in str(excinfo.value)


def test_usuario_constructor():
    usuario = Usuario(
        nombre="Juan",
        fecha_nacimiento="1990-01-01",
        rol="admin",
        correo="juan@example.com",
        contrasena="1234"
    )
    
    assert usuario.nombre == "Juan"
    assert usuario.fecha_nacimiento == "1990-01-01"
    assert usuario.rol == "admin"
    assert usuario.correo == "juan@example.com"
    assert usuario.contrasena == "1234"




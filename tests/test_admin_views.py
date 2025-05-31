import pytest
from app_web.sistema import app
from app_web.extension import pgdb
from app_web.models.admin.usuario_admin import Usuario, UsuarioException
from app_web.models.admin.producto_admin import Producto, ProductoNoEncontradoException
from flask import session, get_flashed_messages, url_for, get_flashed_messages, request
from html import unescape
from app_web.views_admin import render_template as original_render
import app_web.views_admin
from unittest.mock import patch

@pytest.fixture
def client():
    # Configuración para testing
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False  # Deshabilitar CSRF para testing

    # Crea un cliente de prueba
    with app.test_client() as client:
        # Establece un contexto de aplicación
        with app.app_context():
            yield client

def test_consulta_productos_sin_errores(client):
    """Prueba que la ruta devuelva un código 200 OK"""
    response = client.get('/consulta_productos')
    assert response.status_code == 200
    # Verifica que se muestra el título de la página
    assert b"Lista de Productos" in response.data

def test_consulta_productos_sin_productos(client):
    """Prueba el caso cuando no hay productos"""
    response = client.get('/consulta_productos')
    assert response.status_code == 200
    # Verifica que no hay mensajes de error flash
    assert not get_flashed_messages()
    # Verifica que se muestra el contenedor de productos
    assert b'class="productos"' in response.data

def test_login_get(client):
    """Prueba el acceso GET a la página de login"""
    response = client.get('/login')
    assert response.status_code == 200
    # Verifica elementos clave de la página de login
    assert b"Iniciar sesi\xc3\xb3n" in response.data  # Título en español con acento
    assert b'name="usuario"' in response.data  # Campo de usuario
    assert b'name="contrasena"' in response.data  # Campo de contraseña
    assert b'type="submit"' in response.data  # Botón de enviar

def test_login_post_invalid(client):
    """Prueba credenciales inválidas"""
    response = client.post('/login', data={
        'usuario': 'noexiste',
        'contrasena': 'incorrecta'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    messages = get_flashed_messages()
    assert len(messages) > 0
    assert "Credenciales incorrectas" in messages[0]

def test_menu_admin_no_auth(client):
    """Prueba acceso no autorizado a menu_admin"""
    response = client.get('/menu_admin', follow_redirects=True)
    assert response.status_code == 200
    # Verifica que fue redirigido a la página de login
    assert b"Iniciar sesi\xc3\xb3n" in response.data
    # Verifica el mensaje flash
    messages = get_flashed_messages()
    assert len(messages) > 0
    assert "Acceso no autorizado" in messages[0]


@pytest.fixture
def admin_session(client):
    with client.session_transaction() as sess:
        sess['rol'] = 1
        sess['usuario'] = 'admin'
    yield client

def test_menu_admin_auth(admin_session):
    response = admin_session.get('/menu_admin')
    html = response.data.decode('utf-8').lower()
    assert response.status_code == 200
    assert "menú administrador" in html
    assert "consultar productos" in html
    assert "insertar producto" in html

# def test_menu_usuario_no_auth(client):
#     """Prueba acceso no autorizado a menu_usuario"""
#     response = client.get('/menu_usuario', follow_redirects=True)
#     assert response.status_code == 200
#     # Verifica mensaje flash
#     messages = get_flashed_messages()
#     assert messages and "Acceso no autorizado" in messages[0]
#     # Verifica que fue redirigido al login
#     assert b"Iniciar sesi\xc3\xb3n" in response.data

# def test_menu_usuario_auth(client):
#     """Prueba acceso autorizado a menu_usuario"""
#     # Simulamos sesión de usuario directamente
#     with client.session_transaction() as sess:
#         sess['rol'] = 2  # Rol de usuario normal
#         sess['usuario'] = 'usuario'
    
#     response = client.get('/menu_usuario')
#     assert response.status_code == 200
#     # Verifica contenido específico de la página de usuario
#     assert b"Lista de Productos" in response.data  # Ajusta según tu template


def test_consulta_productos_exitoso(client):
    response = client.get('/consulta_productos')
    assert response.status_code == 200
    assert b"Lista de Productos" in response.data or b"class=\"productos\"" in response.data

def test_consulta_productos_no_encontrado(monkeypatch, client):
    # Patch para que lance ProductoNoEncontradoException sin usar mocker
    def fake_consulta_prod():
        raise ProductoNoEncontradoException("No hay productos")
    Producto.consulta_prod = fake_consulta_prod

    response = client.get('/consulta_productos')
    assert response.status_code == 200
    assert b"No hay productos" in response.data or b"class=\"productos\"" in response.data

def test_consulta_productos_error_general(monkeypatch, client):
    def fake_consulta_prod():
        raise Exception("Error inesperado")
    Producto.consulta_prod = fake_consulta_prod

    response = client.get('/consulta_productos')
    assert response.status_code == 200
    assert b"Error al consultar productos" in response.data


## pruebas login 
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False  # Deshabilitar CSRF para testing
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_login_invalid_credentials(client):
    """Prueba login con credenciales inválidas"""
    response = client.post('/login', data={
        'usuario': 'no_existo',
        'contrasena': 'contrasena_invalida'
    }, follow_redirects=True)
    
    messages = get_flashed_messages(with_categories=True)
    assert any('danger' in category and 'Credenciales incorrectas' in message 
              for category, message in messages)

def test_login_with_exception(client):
    """Prueba que el login maneje excepciones sin monkeypatch"""
    # Para probar excepciones sin monkeypatch, necesitas:
    # 1. Configurar condiciones que provoquen la excepción
    # 2. O modificar temporalmente el código (no recomendado)
    
    # Ejemplo: prueba con base de datos no disponible
    # (esto depende de tu implementación real)
    original_method = Usuario.verificar_usuario
    
    try:
        # Modificación temporal solo para prueba (alternativa a monkeypatch)
        def mock_verificar_usuario(username, password):
            raise UsuarioException("Error de prueba")
        
        Usuario.verificar_usuario = mock_verificar_usuario
        
        response = client.post('/login', data={
            'usuario': 'test',
            'contrasena': 'test'
        }, follow_redirects=True)
        
        messages = get_flashed_messages(with_categories=True)
        assert any('danger' in category and 'Error de prueba' in message 
                  for category, message in messages)
    
    finally:
        # Restaurar método original
        Usuario.verificar_usuario = original_method

def test_login_generic_exception(client):
    """Prueba que el login maneje excepciones genéricas"""
    original_method = Usuario.verificar_usuario
    
    try:
        def mock_verificar_usuario(username, password):
            raise Exception("Error inesperado")
        
        Usuario.verificar_usuario = mock_verificar_usuario
        
        response = client.post('/login', data={
            'usuario': 'test',
            'contrasena': 'test'
        }, follow_redirects=True)
        
        messages = get_flashed_messages(with_categories=True)
        assert any('danger' in category and 'Error al intentar iniciar sesión' in message 
                  for category, message in messages)
    
    finally:
        Usuario.verificar_usuario = original_method


# def test_login_successful_admin_and_user(client):
#     # Simular un usuario admin
#     admin_user = {
#         'id': 1,
#         'nombre': 'Admin Test',
#         'correo': 'admin@test.com',
#         'rol': 1
#     }
#     # Simular un usuario normal
#     normal_user = {
#         'id': 2,
#         'nombre': 'User Test',
#         'correo': 'user@test.com',
#         'rol': 2
#     }

#     original_method = Usuario.verificar_usuario

#     try:
#         # Mock para admin
#         Usuario.verificar_usuario = lambda u, p: admin_user if u == 'admin@test.com' and p == 'pass' else None
#         response = client.post('/login', data={'usuario': 'admin@test.com', 'contrasena': 'pass'}, follow_redirects=False)
#         assert response.status_code == 302
#         assert response.headers['Location'].endswith('/menu_admin')

#         with client.session_transaction() as sess:
#             assert sess['usuario'] == admin_user['nombre']
#             assert sess['correo'] == admin_user['correo']
#             assert sess['rol'] == admin_user['rol']
#             assert sess['usuario_id'] == admin_user['id']

#         # Mock para usuario normal
#         Usuario.verificar_usuario = lambda u, p: normal_user if u == 'user@test.com' and p == 'pass' else None
#         response = client.post('/login', data={'usuario': 'user@test.com', 'contrasena': 'pass'}, follow_redirects=False)
#         assert response.status_code == 302
#         assert response.headers['Location'].endswith('/menu_usuario')

#         with client.session_transaction() as sess:
#             assert sess['usuario'] == normal_user['nombre']
#             assert sess['correo'] == normal_user['correo']
#             assert sess['rol'] == normal_user['rol']
#             assert sess['usuario_id'] == normal_user['id']

#     finally:
#         Usuario.verificar_usuario = original_method


def test_login_invalid_role(client):
    # Simular un usuario con rol inválido
    invalid_role_user = {
        'id': 3,
        'nombre': 'Invalid Role',
        'correo': 'invalid@test.com',
        'rol': 3  # Rol que no está contemplado en el login
    }

    original_method = Usuario.verificar_usuario

    try:
        Usuario.verificar_usuario = lambda u, p: invalid_role_user if u == 'invalid@test.com' and p == 'pass' else None

        response = client.post('/login', data={
            'usuario': 'invalid@test.com',
            'contrasena': 'pass'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert "Rol no válido" in response.data.decode('utf-8')

    finally:
        Usuario.verificar_usuario = original_method


##pruebas menu no borrar


# def test_menu_usuario_generic_exception(client, monkeypatch):
#     """Prueba manejo de excepciones genéricas en menu_usuario"""
#     # Configuramos el mock para lanzar una excepción genérica
#     def mock_consulta_prod():
#         raise Exception("Error inesperado en la base de datos")
    
#     monkeypatch.setattr(Producto, 'consulta_prod', mock_consulta_prod)
    
#     # Simulamos sesión de usuario normal
#     with client.session_transaction() as sess:
#         sess['rol'] = 2
#         sess['usuario'] = 'usuario_test'
    
#     response = client.get('/menu_usuario', follow_redirects=True)
    
#     # Verificamos el comportamiento esperado
#     assert response.status_code == 200
#     assert b"Iniciar sesi\xc3\xb3n" in response.data  # Verifica redirección
#     messages = get_flashed_messages(with_categories=True)
#     assert len(messages) > 0
#     assert "Error al acceder al menú de usuario" in messages[0][1]

# def test_menu_usuario_producto_no_encontrado(client, monkeypatch):
#     """Prueba que verifica el manejo de ProductoNoEncontradoException"""
#     # Mock para simular la excepción
#     def mock_consulta_prod():
#         raise ProductoNoEncontradoException("No hay productos disponibles")
    
#     monkeypatch.setattr(Producto, 'consulta_prod', mock_consulta_prod)
    
#     # Sesión de usuario con rol correcto
#     with client.session_transaction() as sess:
#         sess['rol'] = 2
#         sess['usuario'] = 'test_user'
    
#     response = client.get('/menu_usuario')
    
#     # Verificaciones clave
#     assert response.status_code == 200
    
#     # Verifica que se muestra el template correcto (busca elementos del HTML)
#     assert b"Lista de Productos" in response.data  # Título de la página
#     assert b'class="productos"' in response.data   # Contenedor de productos
    
#     # Verifica el mensaje flash
#     messages = get_flashed_messages(with_categories=True)
#     assert len(messages) == 1
#     assert messages[0][0] == 'danger'  # Categoría
#     assert "No hay productos disponibles" in messages[0][1]  # Mensaje

# def test_menu_usuario_excepcion_generica(client):
#     """Prueba que se manejan correctamente las excepciones genéricas"""
#     # Guardamos el método original para restaurarlo después
#     original_consulta_prod = Producto.consulta_prod
    
#     try:
#         # Mockeamos el método para que lance una excepción genérica
#         def mock_consulta_prod():
#             raise Exception("Error de conexión con la base de datos")
        
#         Producto.consulta_prod = mock_consulta_prod
        
#         # Simulamos sesión de usuario normal (rol 2)
#         with client.session_transaction() as sess:
#             sess['rol'] = 2
#             sess['usuario'] = 'usuario_test'
        
#         response = client.get('/menu_usuario', follow_redirects=True)
        
#         # Verificamos el comportamiento esperado
#         assert response.status_code == 200
#         assert b"Iniciar sesi\xc3\xb3n" in response.data  # Verifica redirección
        
#         # Verificamos el mensaje flash
#         messages = get_flashed_messages(with_categories=True)
#         assert len(messages) == 1
#         category, message = messages[0]
#         assert category == 'danger'
#         assert "Error al acceder al menú de usuario: Error de conexión con la base de datos" in message
    
#     finally:
#         # Restauramos el método original
#         Producto.consulta_prod = original_consulta_prod
        

#probando

# def test_menu_admin_exception_handling(client):
#     """Versión que no usa monkeypatch"""
#     # 2. Creamos el mock
#     def mock_render(*args, **kwargs):
#         raise Exception("Error simulado")
    
#     try:
#         # 3. Reemplazamos la función
#         app_web.views_admin.render_template = mock_render
        
#         # 4. Configuramos sesión
#         with client.session_transaction() as sess:
#             sess['rol'] = 1
#             sess['usuario'] = 'admin_test'
        
#         # 5. Hacemos la petición
#         response = client.get('/menu_admin', follow_redirects=True)
        
#         # 6. Verificaciones
#         assert response.status_code == 200
#         assert b"Iniciar sesi\xc3\xb3n" in response.data
        
#         # Verificar mensaje flash
#         messages = get_flashed_messages(with_categories=True)
#         assert len(messages) == 1
#         assert "Error al acceder al menú de administrador" in messages[0][1]
    
#     finally:
#         # 7. Restauramos la función original
#         app_web.views_admin.render_template = original_render


# insertar usuario

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False  # Deshabilitar CSRF para testing
    
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_insertar_usuario_post_failure(client):
    """Prueba cuando falla el registro por error desconocido"""
    data = {
        'nombre': 'Test User',
        'fecha_nacimiento': '2000-01-01',
        'rol': 'user',
        'correo': 'test@example.com',
        'contrasena': 'password123'
    }
    
    original_method = Usuario.insertar_usuario_en_db
    Usuario.insertar_usuario_en_db = lambda *args: False
    
    response = client.post('/insertar_usuario', data=data)
    
    assert response.status_code == 200
    messages = get_flashed_messages(with_categories=True)
    assert len(messages) == 1
    assert messages[0][1] == "No se pudo registrar el usuario por un error desconocido."
    
    Usuario.insertar_usuario_en_db = original_method

def test_insertar_usuario_post_exception(client):
    """Prueba cuando ocurre una excepción conocida"""
    data = {
        'nombre': 'Test User',
        'fecha_nacimiento': '2000-01-01',
        'rol': 'user',
        'correo': 'test@example.com',
        'contrasena': 'password123'
    }
    
    original_method = Usuario.insertar_usuario_en_db
    Usuario.insertar_usuario_en_db = lambda *args: (_ for _ in ()).throw(
        UsuarioException("Error específico de usuario"))
    
    response = client.post('/insertar_usuario', data=data)
    
    assert response.status_code == 200
    messages = get_flashed_messages(with_categories=True)
    assert len(messages) == 1
    assert messages[0][1] == "Error específico de usuario"
    
    Usuario.insertar_usuario_en_db = original_method

def test_insertar_usuario_post_general_exception(client):
    """Prueba cuando ocurre una excepción genérica"""
    data = {
        'nombre': 'Test User',
        'fecha_nacimiento': '2000-01-01',
        'rol': 'user',
        'correo': 'test@example.com',
        'contrasena': 'password123'
    }
    
    original_method = Usuario.insertar_usuario_en_db
    Usuario.insertar_usuario_en_db = lambda *args: (_ for _ in ()).throw(Exception())
    
    response = client.post('/insertar_usuario', data=data)
    
    assert response.status_code == 200
    messages = get_flashed_messages(with_categories=True)
    assert len(messages) == 1
    assert messages[0][1] == "Ocurrió un error inesperado al registrar el usuario."
    
    Usuario.insertar_usuario_en_db = original_method

def test_insertar_usuario_post_successful_registration(client):
    """Prueba el flujo completo cuando el registro de usuario es exitoso"""
    # Datos de prueba válidos
    user_data = {
        'nombre': 'Juan Perez',
        'fecha_nacimiento': '1990-05-15',
        'rol': '2',
        'correo': 'juan@example.com',
        'contrasena': 'securepassword123'
    }
    
    # Guardamos el método original para restaurarlo después
    original_insert = Usuario.insertar_usuario_en_db
    
    # Configuramos el método para que retorne True (éxito)
    Usuario.insertar_usuario_en_db = lambda *args, **kwargs: True
    
    try:
        # Hacemos la petición POST con follow_redirects=False para verificar la redirección
        response = client.post('/insertar_usuario', data=user_data, follow_redirects=False)
        
        # Verificamos la redirección (código 302)
        assert response.status_code == 302
        assert url_for('login_home') in response.location
        
        # Hacemos otra petición siguiendo la redirección para verificar el mensaje flash
        redirected_response = client.post('/insertar_usuario', data=user_data, follow_redirects=True)
        messages = get_flashed_messages(with_categories=True)
        
        # Verificamos el mensaje flash
        assert len(messages) == 2
        assert messages[0][0] == 'success'
        assert messages[0][1] == "Usuario registrado correctamente."
        
        # Verificamos que estamos en la página de login
        assert url_for('login_home') in redirected_response.request.url
        
    finally:
        # Restauramos el método original
        Usuario.insertar_usuario_en_db = original_insert

 # Perfil del usuario

def test_perfil_usuario_con_sesion(client):
    """Prueba acceso a perfil cuando hay usuario en sesión"""
    # Establecemos datos de sesión
    with client.session_transaction() as sess:
        sess['usuario'] = 'Juan Perez'
        sess['correo'] = 'juan@example.com'
    
    response = client.get('/perfil_usuario')
    
    assert response.status_code == 200
    # Verificamos los datos en el contenido renderizado
    assert b'Juan Perez' in response.data
    assert b'juan@example.com' in response.data
    assert b'Perfil del Usuario' in response.data

def test_perfil_usuario_sin_sesion(client):
    """Prueba acceso a perfil cuando NO hay usuario en sesión"""
    response = client.get('/perfil_usuario', follow_redirects=True)
    
    # Verificar que estamos en la página de login
    assert response.status_code == 200
    assert b'Iniciar sesi\xc3\xb3n' in response.data  # Verifica el título del formulario de login
    assert b'action="/login"' in response.data  # Verifica el formulario de login
    
    # Verificar mensaje flash
    messages = get_flashed_messages(with_categories=True)
    assert len(messages) == 1
    assert messages[0][0] == 'warning'
    assert messages[0][1] == "Primero inicia sesión para ver tu perfil."

 # Cerrar sesión

def test_logout_exitoso(client):
    """Prueba que el cierre de sesión funciona correctamente"""
    # Primero establecemos una sesión activa
    with client.session_transaction() as sess:
        sess['usuario'] = 'test_user'
        sess['correo'] = 'test@example.com'
    
    # Hacemos la petición POST a logout
    response = client.post('/logout', follow_redirects=True)
    
    # Verificamos que la sesión está vacía
    with client.session_transaction() as sess:
        assert 'usuario' not in sess
        assert 'correo' not in sess
    
    # Verificamos la redirección
    assert response.status_code == 200
    assert b'Iniciar sesi\xc3\xb3n' in response.data  # Verificamos que estamos en login
    
    # Verificamos el mensaje flash
    messages = get_flashed_messages(with_categories=True)
    assert len(messages) == 1
    assert messages[0][0] == 'info'
    assert messages[0][1] == "Has cerrado sesión exitosamente."

# Página de la consulta de stock productos

def test_consulta_stock_sin_sesion(client):
    """Prueba acceso sin sesión activa"""
    response = client.get('/consulta_stock', follow_redirects=True)
    
    # Verificar redirección a login
    assert response.status_code == 200
    assert b'Iniciar sesi\xc3\xb3n' in response.data
    
    # Verificar mensaje flash
    messages = get_flashed_messages(with_categories=True)
    assert len(messages) == 1
    assert messages[0][0] == 'danger'
    assert messages[0][1] == "Acceso no autorizado"

def test_consulta_stock_con_sesion_sin_productos(client):
    """Prueba con sesión activa pero sin productos"""
    # Establecer sesión con rol adecuado (1)
    with client.session_transaction() as sess:
        sess['usuario_id'] = 123
        sess['rol'] = 1  # Añadir rol requerido
    
    # Configurar comportamiento esperado
    original_method = Producto.consulta_prod_por_usuario
    Producto.consulta_prod_por_usuario = lambda usuario_id: []
    
    try:
        response = client.get('/consulta_stock', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Lista de Productos' in response.data
        
    finally:
        # Restaurar método original
        Producto.consulta_prod_por_usuario = original_method


def test_consulta_stock_con_excepcion_producto_no_encontrado(client):
    """Prueba cuando se lanza ProductoNoEncontradoException"""
    # Establecer sesión con rol adecuado (1)
    with client.session_transaction() as sess:
        sess['usuario_id'] = 123
        sess['rol'] = 1
    
    # Configurar comportamiento esperado
    original_method = Producto.consulta_prod_por_usuario
    Producto.consulta_prod_por_usuario = lambda usuario_id: (_ for _ in ()).throw(
        ProductoNoEncontradoException("No se encontraron productos"))
    
    try:
        response = client.get('/consulta_stock', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Lista de Productos' in response.data
        
        # Verificar mensaje flash
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0][0] == 'info'
        assert "No se encontraron productos" in messages[0][1]
        
    finally:
        # Restaurar método original
        Producto.consulta_prod_por_usuario = original_method

def test_consulta_stock_con_excepcion_general(client):
    """Prueba cuando ocurre una excepción inesperada"""
    # Establecer sesión con rol adecuado (1)
    with client.session_transaction() as sess:
        sess['usuario_id'] = 123
        sess['rol'] = 1
    
    # Configurar comportamiento esperado
    original_method = Producto.consulta_prod_por_usuario
    Producto.consulta_prod_por_usuario = lambda usuario_id: (_ for _ in ()).throw(
        Exception("Error inesperado"))
    
    try:
        response = client.get('/consulta_stock', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Lista de Productos' in response.data
        
        # Verificar mensaje flash
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0][0] == 'danger'
        assert "Error al consultar productos" in messages[0][1]
        
    finally:
        # Restaurar método original
        Producto.consulta_prod_por_usuario = original_method

# Detalle de la consulta de productos para editar


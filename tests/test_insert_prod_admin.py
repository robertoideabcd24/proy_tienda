import pytest
from flask import session, url_for, get_flashed_messages
from decimal import Decimal
from app_web.models.admin.producto_admin import Producto
from app_web.models.admin.producto_admin import AltaProductoPrecioException

@pytest.fixture
def admin_session(client):
    """Sesión de usuario con rol de administrador"""
    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 1  # Rol de admin
        sess['usuario'] = 'admin_test'
    yield client


# probado
def test_insertar_producto_get_con_auth(admin_session):
    """Prueba acceso GET con sesión de admin"""
    response = admin_session.get('/insertar_producto')
    assert response.status_code == 200
    assert b"Insertar Producto" in response.data  # Ajusta según tu template

# probado
def test_insertar_producto_post_valido(admin_session):
    data = {
        'nombre': 'Producto Test',
        'precio': '100.50',
        'disponible': 'on',
        'marca': 'Marca Test',
        'descripcion': 'Descripción de prueba'
    }

    with admin_session:
        response = admin_session.post('/insertar_producto', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b"Lista de Productos" in response.data
        # Verifica que el producto aparece en la lista
        assert b"Producto Test" in response.data
        assert b"100.50" in response.data
        
# probado
def test_insertar_producto_post_excepcion_no_controlada(admin_session):
    """Prueba cuando ocurre una excepción no controlada"""
    data = {
        'nombre': 'Producto Test',
        'precio': '100.50',
        'disponible': 'on',
        'marca': 'Marca Test',
        'descripcion': 'Descripción de prueba'
    }
    
    # Guardamos el método original
    original_method = Producto.insertar_producto_en_db
    
    try:
        # Configuramos el método para que lance una excepción
        Producto.insertar_producto_en_db = lambda *args, **kwargs: (_ for _ in ()).throw(Exception("Error inesperado"))
        
        response = admin_session.post('/insertar_producto', data=data, follow_redirects=True)
        assert b"Error inesperado" in response.data
    
    finally:
        # Restauramos el método original
        Producto.insertar_producto_en_db = original_method


def test_insertar_producto_post_precio_invalido(admin_session):
    data = {
        'nombre': 'Producto Test',
        'precio': '-100.50',
        'disponible': 'on',
        'marca': 'Marca Test',
        'descripcion': 'Descripción de prueba'
    }

    response = admin_session.post('/insertar_producto', data=data, follow_redirects=True)
    assert b"el precio no puede ser negativo" in response.data

def test_insertar_producto_post_descripcion_vacia(admin_session):
    data = {
        'nombre': 'Producto Test',
        'precio': '100.50',
        'disponible': 'on',
        'marca': 'Marca Test',
        'descripcion': ''
    }

    response = admin_session.post('/insertar_producto', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert "la descripción no puede estar vacía".encode("utf-8") in response.data

def test_insertar_producto_get_no_auth(client):
    response = client.get('/insertar_producto', follow_redirects=True)
    assert response.status_code == 200
    assert b"Iniciar sesi\xc3\xb3n" in response.data
    assert b"Acceso no autorizado" in response.data


# # fallando

def test_insertar_producto_post_nombre_vacio(admin_session):
    data = {
        'nombre': '',
        'precio': '100.50',
        'disponible': 'on',
        'marca': 'Marca Test',
        'descripcion': 'Descripción de prueba'
    }

    response = admin_session.post('/insertar_producto', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert "El nombre no puede estar vacío".encode("utf-8") in response.data


def test_insertar_producto_post_precio_vacio(admin_session):
    data = {
        'nombre': 'Producto Test',
        'precio': '',
        'disponible': 'on',
        'marca': 'Marca Test',
        'descripcion': 'Descripción de prueba'
    }

    response = admin_session.post('/insertar_producto', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert "El precio no puede estar vacío".encode("utf-8") in response.data

def test_insertar_producto_post_precio_no_numerico(admin_session):
    data = {
        'nombre': 'Producto Test',
        'precio': 'abc',
        'disponible': 'on',
        'marca': 'Marca Test',
        'descripcion': 'Descripción de prueba'
    }

    response = admin_session.post('/insertar_producto', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert "El precio debe ser un número".encode("utf-8") in response.data

def test_insertar_producto_post_error_en_insertar(admin_session):
    # Simular que el método devuelve False
    original_method = Producto.insertar_producto_en_db
    Producto.insertar_producto_en_db = lambda *args, **kwargs: False

    data = {
        'nombre': 'Producto Test',
        'precio': '100.50',
        'disponible': 'on',
        'marca': 'Marca Test',
        'descripcion': 'Descripción de prueba'
    }

    try:
        response = admin_session.post('/insertar_producto', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b"Ocurri\xc3\xb3 un error al insertar el producto." in response.data
    finally:
        Producto.insertar_producto_en_db = original_method

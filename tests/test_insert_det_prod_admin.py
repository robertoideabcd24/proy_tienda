import pytest

from app_web.models.admin.producto_admin import Producto
from app_web.models.admin.producto_admin import AltaProductoPrecioException

from flask import session, url_for, get_flashed_messages

@pytest.fixture
def admin_session(client):
    """Sesión de administrador iniciada"""
    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 1
        sess['usuario'] = 'admin_test'
    yield client

@pytest.fixture
def producto_de_prueba():
    
    nombre = "Producto Detalle Test"
    precio = 99.99
    disponible = True
    marca = "Marca Test"
    descripcion = "Producto para prueba de detalles"
    usuario_id = 1

    producto_id = Producto.insertar_producto_en_db(nombre, precio, disponible, marca, descripcion, usuario_id)
    
    # Asegurarse de que se obtuvo un ID válido
    assert isinstance(producto_id, int)
    return producto_id


# -------------------------------
# GET con autenticación y producto válido
# -------------------------------
def test_get_insertar_detalles_producto_valido(admin_session, producto_de_prueba):
    response = admin_session.get(f'/insertar_detalles_producto/{producto_de_prueba}')
    assert response.status_code == 200
    assert b"Insertar Detalles" in response.data or b"Talla" in response.data

# -------------------------------
# POST exitoso
# -------------------------------
def test_post_insertar_detalles_producto_valido(admin_session, producto_de_prueba):
    data = {
        'talla': 'M',
        'color': 'Negro',
        'stock': '10'
    }

    response = admin_session.post(f'/insertar_detalles_producto/{producto_de_prueba}', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Detalle del producto insertado correctamente" in response.data

# -------------------------------
# POST falla al insertar detalle
# -------------------------------
def test_post_insertar_detalles_producto_falla(admin_session, producto_de_prueba):
   
    data = {
        'talla': 'XL',
        'color': 'Rojo',
        'stock': ''  
    }

    response = admin_session.post(f'/insertar_detalles_producto/{producto_de_prueba}', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Error al insertar detalles del producto" in response.data or b"Ocurri\xc3\xb3 un error" in response.data

# -------------------------------
# Producto no existe
# -------------------------------
def test_insertar_detalles_producto_producto_no_existente(admin_session):
    producto_id = 99999  

    response = admin_session.get(f'/insertar_detalles_producto/{producto_id}', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/consulta_stock')


import pytest
from flask import Flask, session, get_flashed_messages
from unittest.mock import patch, MagicMock
from decimal import Decimal
import os
import sys

# Asegura que app_web se puede importar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_web.sistema import create_app
from app_web.views_usuario import registrar_rutas_usuario
from app_web.views_admin import registrar_rutas as registrar_admin

# ============================= FIXTURES ===================================

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    registrar_admin(app)
    registrar_rutas_usuario(app)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def set_session(client):
    with client.session_transaction() as sess:
        sess['rol'] = 2
        sess['usuario_id'] = 1

# ======================= TESTS FUNCIONALES DE USUARIO ==========================

@pytest.mark.parametrize("producto_data, precio_esperado", [
    ({'id': 1, 'precio': 100}, 100.0),
    ({'id': 1}, 0.0),
    (None, 0.0),
    ({'id': 1, 'precio': '150'}, 150.0),
])
@patch('app_web.views_usuario.Producto.actualizar_stock')
@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
@patch('app_web.views_usuario.Carrito.agregar_producto')
@patch('app_web.views_usuario.Compra.guardar_compra')
def test_agregar_carrito_precio(
    mock_guardar_compra,
    mock_agregar_producto,
    mock_obtener_producto,
    mock_obtener_detalles,
    mock_actualizar_stock,
    client,
    app,
    producto_data,
    precio_esperado
):
    mock_obtener_detalles.return_value = [('M', 'Rojo', 10)]
    mock_obtener_producto.return_value = producto_data
    mock_guardar_compra.return_value = (True, "Éxito")
    mock_actualizar_stock.return_value = (True, "Stock actualizado")
    
    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 2

    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '0',
        'cantidad_0': '2',
        'accion': 'comprar'
    })
    
    assert response.status_code == 302
    assert response.location.endswith('/comprar/1')

    if producto_data is not None:
        args, _ = mock_guardar_compra.call_args
        assert float(args[5]) == precio_esperado

@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
@patch('app_web.views_usuario.Carrito.agregar_producto')
@patch('app_web.views_usuario.Compra.guardar_compra')
def test_agregar_carrito(
    mock_guardar_compra,
    mock_agregar_producto,
    mock_obtener_producto,
    mock_obtener_detalles,
    client,
    app
):
    mock_obtener_detalles.return_value = [('M', 'Rojo', 10), ('L', 'Azul', 5)]
    mock_obtener_producto.return_value = {'id': 1, 'precio': 100}
    mock_guardar_compra.return_value = (True, "Éxito")

    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 2

    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '0',
        'cantidad_0': '2',
        'accion': 'comprar'
    })

    assert response.status_code == 302
    assert response.location.endswith('/comprar/1')

# ============================= VIEWS Y ERRORES =============================

@patch('app_web.views_usuario.render_template')
@patch('app_web.views_usuario.Carrito.obtener_todos_por_usuario')
def test_ver_carrito(mock_obtener_carrito, mock_render_template, client, set_session):
    mock_obtener_carrito.return_value = [{
        'nombre': 'Producto Test',
        'precio_original': 100,
        'precio_final': 90,
        'descuento_porcentaje': 10,
        'talla': 'M',
        'color': 'Rojo',
        'cantidad': 1,
        'subtotal': 90
    }]
    mock_render_template.return_value = "Template Simulado"

    response = client.get('/ver_carrito')
    assert response.status_code == 200
    assert b'Template Simulado' in response.data

@patch('app_web.views_usuario.Carrito.procesar_pago')
def test_pagar_carrito(mock_procesar_pago, client, set_session):
    mock_procesar_pago.return_value = (True, "Pago exitoso")
    response = client.post('/pagar_carrito')
    assert response.status_code == 302
    assert 'ver_carrito' in response.location

@patch('app_web.views_usuario.Carrito.eliminar_producto')
def test_eliminar_del_carrito(mock_eliminar, client, set_session):
    response = client.post('/eliminar_del_carrito', data={
        'producto_id': '1',
        'talla': 'M',
        'color': 'Rojo'
    })
    assert mock_eliminar.called
    assert response.status_code == 302

@patch('app_web.views_usuario.render_template')
@patch('app_web.views_usuario.Compra.obtener_compras_usuario')
def test_ver_compras(mock_obtener_compras, mock_render_template, client, set_session):
    mock_obtener_compras.return_value = [{'nombre': 'Producto Comprado', 'fecha': '2023-01-01'}]
    mock_render_template.return_value = "Template Simulado"

    response = client.get('/ver_compras')
    assert response.status_code == 200
    assert b'Template Simulado' in response.data

# ========================== ERRORES Y FLASH MESSAGES ============================

def test_agregar_carrito_cantidad_cero(client, set_session):
    with patch('app_web.models.admin.producto_admin.Producto.obtener_detalles_por_id') as mock_detalles:
        mock_detalles.return_value = [('M', 'Rojo', 10)]
        response = client.post('/agregar_carrito/1', data={
            'detalle_seleccionado': '0',
            'cantidad_0': '0'
        }, follow_redirects=True)
        assert b'La cantidad debe ser mayor a cero' in response.data

# (Agrega aquí los otros tests de errores y casos borde si quieres que los incluya también)


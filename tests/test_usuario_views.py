import pytest
from unittest.mock import patch
from flask import Flask, session, url_for
from app_web.views_usuario import registrar_rutas_usuario
from app_web.views_admin import registrar_rutas as registrar_admin
import pytest
import sys
import os
from flask import session, get_flashed_messages
from unittest.mock import patch, MagicMock
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


import pytest
from flask import session, get_flashed_messages
from unittest.mock import patch, MagicMock

# Añadir el directorio principal al path para resolver importaciones
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_web.sistema import create_app

# Añadir el directorio principal al path para resolver importaciones
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_web.sistema import create_app


import pytest
import sys
import os
from flask import session, get_flashed_messages
from unittest.mock import patch, MagicMock

# Añadir el directorio principal al path para resolver importaciones
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_web.sistema import create_app


# Configuración básica de la aplicación de prueba
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret'
    
    registrar_admin(app)
    registrar_rutas_usuario(app)

    return app

@pytest.fixture
def client(app):
    return app.test_client()

# Prueba parametrizada para diferentes escenarios de precio
@pytest.mark.parametrize("producto_data, precio_esperado", [
    # Caso 1: Producto con precio válido
    ({'id': 1, 'precio': 100}, 100.0),
    # Caso 2: Producto sin clave 'precio'
    ({'id': 1}, 0.0),
    # Caso 3: Producto no encontrado (None)
    (None, 0.0),
    # Caso 4: Precio como string (convertido a float)
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
    # Configurar mocks comunes
    mock_obtener_detalles.return_value = [('M', 'Rojo', 10)]
    mock_obtener_producto.return_value = producto_data
    mock_guardar_compra.return_value = (True, "Éxito")
    mock_actualizar_stock.return_value = (True, "Stock actualizado")
    
    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 2

    # Realizar la acción de compra
    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '0',
        'cantidad_0': '2',
        'accion': 'comprar'
    })
    
    # Verificar redirección
    assert response.status_code == 302
    assert response.location.endswith('/comprar/1')
    
    # Verificar que se llamó a guardar_compra con el precio esperado
    if producto_data is not None:
        # Verificar los argumentos sin importar el tipo exacto
        args, kwargs = mock_guardar_compra.call_args
        assert args[0] == 1  # usuario_id
        assert args[1] == 1  # producto_id
        assert args[2] == 'M'  # talla
        assert args[3] == 'Rojo'  # color
        assert args[4] == 2  # cantidad
        # Comprobar el precio como float
        assert float(args[5]) == precio_esperado
# Prueba original para agregar al carrito
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
    mock_obtener_detalles.return_value = [
        ('M', 'Rojo', 10),
        ('L', 'Azul', 5)
    ]
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


@patch('app_web.views_usuario.render_template')
@patch('app_web.views_usuario.Carrito.obtener_todos_por_usuario')
def test_ver_carrito(mock_obtener_carrito, mock_render_template, client):
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
    
    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 2

    response = client.get('/ver_carrito')
    assert response.status_code == 200
    assert b'Template Simulado' in response.data

@patch('app_web.views_usuario.Carrito.procesar_pago')
def test_pagar_carrito(mock_procesar_pago, client):
    mock_procesar_pago.return_value = (True, "Pago exitoso")
    
    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 2

    response = client.post('/pagar_carrito')
    assert response.status_code == 302
    assert 'ver_carrito' in response.location

@patch('app_web.views_usuario.Carrito.eliminar_producto')
def test_eliminar_del_carrito(mock_eliminar, client):
    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 2

    response = client.post('/eliminar_del_carrito', data={
        'producto_id': '1',
        'talla': 'M',
        'color': 'Rojo'
    })
    assert mock_eliminar.called
    assert response.status_code == 302

@patch('app_web.views_usuario.render_template')
@patch('app_web.views_usuario.Compra.obtener_compras_usuario')
def test_ver_compras(mock_obtener_compras, mock_render_template, client):
    mock_obtener_compras.return_value = [{
        'nombre': 'Producto Comprado',
        'fecha': '2023-01-01'
    }]
    mock_render_template.return_value = "Template Simulado"
    
    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 2

    response = client.get('/ver_compras')
    assert response.status_code == 200
    assert b'Template Simulado' in response.data


#======================# test de views_usuario flash==================================================================


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def set_session(client):
    with client.session_transaction() as sess:
        sess['rol'] = 2
        sess['usuario_id'] = 1



# test de views_usuario

# Nuevas pruebas para cubrir mensajes flash y casos de error

def test_agregar_carrito_cantidad_cero(client, set_session):
    with patch('app_web.models.admin.producto_admin.Producto.obtener_detalles_por_id') as mock_detalles:
        mock_detalles.return_value = [('M', 'Rojo', 10)]
        data = {
            'detalle_seleccionado': '0',
            'cantidad_0': '0',  # Cantidad cero
        }
        response = client.post('/agregar_carrito/1', data=data, follow_redirects=True)
        assert b'La cantidad debe ser mayor a cero' in response.data

def test_agregar_carrito_usuario_no_autenticado(client):
    # No establecemos sesión
    with patch('app_web.models.admin.producto_admin.Producto.obtener_detalles_por_id') as mock_detalles:
        mock_detalles.return_value = [('M', 'Rojo', 10)]
        data = {
            'detalle_seleccionado': '0',
            'cantidad_0': '2',
        }
        response = client.post('/agregar_carrito/1', data=data, follow_redirects=True)
        assert b'Usuario no autenticado' in response.data

@patch('app_web.models.admin.producto_admin.Producto.actualizar_stock')
@patch('app_web.models.admin.producto_admin.Producto.obtener_detalles_por_id')
def test_agregar_carrito_actualizacion_stock_fallida(mock_detalles, mock_actualizar_stock, client, set_session):
    mock_detalles.return_value = [('M', 'Rojo', 10)]
    mock_actualizar_stock.return_value = (False, "Error en stock")

    data = {
        'detalle_seleccionado': '0',
        'cantidad_0': '2',
        'accion': 'comprar'
    }
    response = client.post('/agregar_carrito/1', data=data, follow_redirects=True)
    assert b'Error en stock' in response.data

@patch('app_web.models.usuario.compras.Compra.guardar_compra')
@patch('app_web.models.admin.producto_admin.Producto.actualizar_stock')
@patch('app_web.models.admin.producto_admin.Producto.obtener_detalles_por_id')
def test_agregar_carrito_guardar_compra_fallida(mock_detalles, mock_actualizar_stock, mock_guardar_compra, client, set_session):
    mock_detalles.return_value = [('M', 'Rojo', 10)]
    mock_actualizar_stock.return_value = (True, "Stock actualizado")
    mock_guardar_compra.return_value = (False, "Error en compra")

    data = {
        'detalle_seleccionado': '0',
        'cantidad_0': '2',
        'accion': 'comprar'
    }
    response = client.post('/agregar_carrito/1', data=data, follow_redirects=True)
    assert b'Error al registrar compra' in response.data

def test_agregar_carrito_excepcion_valor(client, set_session):
    with patch('app_web.models.admin.producto_admin.Producto.obtener_detalles_por_id') as mock_detalles:
        mock_detalles.return_value = [('M', 'Rojo', 10)]
        data = {
            'detalle_seleccionado': '0',
            'cantidad_0': 'no-numerico',  # Valor inválido
        }
        response = client.post('/agregar_carrito/1', data=data, follow_redirects=True)
        assert b'Cantidad inv' in response.data  # "Cantidad inválida"

@patch('app_web.models.admin.producto_admin.Producto.obtener_detalles_por_id')
def test_agregar_carrito_excepcion_general(mock_detalles, client, set_session):
    mock_detalles.side_effect = Exception("Error inesperado")
    data = {
        'detalle_seleccionado': '0',
        'cantidad_0': '2',
    }
    response = client.post('/agregar_carrito/1', data=data, follow_redirects=True)
    assert b'Error: Error inesperado' in response.data

def test_ver_carrito_no_autenticado(client):
    response = client.get('/ver_carrito', follow_redirects=True)
    assert b'Debes iniciar sesi' in response.data  # "Debes iniciar sesión"

@patch('app_web.models.usuario.carrito_usuario.Carrito.procesar_pago')
def test_pagar_carrito_fallido(mock_procesar_pago, client, set_session):
    mock_procesar_pago.return_value = (False, "Error en pago")
    response = client.post('/pagar_carrito', follow_redirects=True)
    assert b'Error en pago' in response.data

@patch('app_web.models.usuario.carrito_usuario.Carrito.eliminar_producto')
def test_eliminar_del_carrito_error(mock_eliminar, client, set_session):
    mock_eliminar.side_effect = Exception("Error al eliminar")
    data = {
        'producto_id': '1',
        'talla': 'M',
        'color': 'Rojo'
    }
    response = client.post('/eliminar_del_carrito', data=data, follow_redirects=True)
    assert b'Error al eliminar' in response.data

def test_ver_compras_no_autenticado(client):
    response = client.get('/ver_compras', follow_redirects=True)
    assert b'Debes iniciar sesi' in response.data  # "Debes iniciar sesión"

@patch('app_web.models.usuario.carrito_usuario.Carrito.obtener_todos_por_usuario')
def test_ver_carrito_error(mock_obtener_carrito, client, set_session):
    mock_obtener_carrito.side_effect = Exception("Error en carrito")
    response = client.get('/ver_carrito', follow_redirects=True)
    assert b'Error al cargar el carrito' in response.data

@patch('app_web.models.usuario.compras.Compra.obtener_compras_usuario')
def test_ver_compras_error(mock_obtener_compras, client, set_session):
    mock_obtener_compras.side_effect = Exception("Error en compras")
    response = client.get('/ver_compras', follow_redirects=True)
    # Verificamos que se redirige a consulta_productos
    assert b'consultar_bien.html' in response.data or b'consultar_prod_usu.html' in response.data





#=========================================================================================================


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def set_session(client):
    with client.session_transaction() as sess:
        sess['rol'] = 2
        sess['usuario_id'] = 1

def test_agregar_carrito_sin_detalle_seleccionado(client, set_session):
    response = client.post('/agregar_carrito/1', data={}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Debes seleccionar una talla y color' in response.data

@patch('app_web.models.admin.producto_admin.Producto.obtener_detalles_por_id')
def test_agregar_carrito_con_indice_invalido(mock_detalles, client, set_session):
    mock_detalles.return_value = [('M', 'Rojo', 5)]
    data = {
        'detalle_seleccionado': '5'  # índice inválido
    }
    response = client.post('/agregar_carrito/1', data=data, follow_redirects=True)
    assert b'Selecci' in response.data  # "Selección inválida"

@patch('app_web.models.admin.producto_admin.Producto.obtener_detalles_por_id')
def test_agregar_carrito_stock_insuficiente(mock_detalles, client, set_session):
    mock_detalles.return_value = [('M', 'Rojo', 2)]
    data = {
        'detalle_seleccionado': '0',
        'cantidad_0': '5',
    }
    response = client.post('/agregar_carrito/1', data=data, follow_redirects=True)
    assert b'No hay suficiente stock' in response.data

@patch('app_web.models.admin.producto_admin.Producto.obtener_detalles_por_id')
def test_agregar_carrito_con_exito(mock_detalles, client, set_session):
    mock_detalles.return_value = [('M', 'Rojo', 10)]

    with patch('app_web.models.usuario.carrito_usuario.Carrito.agregar_producto') as mock_add:
        data = {
            'detalle_seleccionado': '0',
            'cantidad_0': '2',
            'accion': 'agregar'
        }
        response = client.post('/agregar_carrito/1', data=data, follow_redirects=True)
        assert b'Producto agregado al carrito' in response.data
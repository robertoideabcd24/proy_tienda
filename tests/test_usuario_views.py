import pytest
from unittest.mock import patch, MagicMock
from flask import session
import sys
import os
from datetime import datetime
from decimal import Decimal
from bs4 import BeautifulSoup
from app_web.models.admin.producto_admin import Producto


# Configurar path para importaciones
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_web.sistema import create_app

# Fixture para la aplicación de prueba
@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test_secret'

    # Registrar endpoint faltante para evitar errores de ruteo
    @app.route('/menu_usuario')
    def menu_usuario():
        return "Mock menu usuario"

    return app

# Fixture para el cliente de prueba
@pytest.fixture
def client(app):
    return app.test_client()

# Fixture para sesión de usuario
@pytest.fixture
def session_user(client):
    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 2
    return sess

# -----------------------------------------------------------
# Pruebas principales para las rutas de usuario (corregidas)
# -----------------------------------------------------------

@patch('app_web.views_usuario.Compra.guardar_compra')
@patch('app_web.views_usuario.Producto.actualizar_stock')
@patch('app_web.views_usuario.Producto.obtener_stock_disponible') 
@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
def test_agregar_carrito(
    mock_obtener_producto,
    mock_obtener_detalles,
    mock_obtener_stock_disponible,  
    mock_actualizar_stock,
    mock_guardar_compra,
    client,
    session_user
):
    
    mock_obtener_detalles.return_value = [('M', 'Rojo', 10)]  # talla, color, stock
    mock_obtener_producto.return_value = {'id': 1, 'precio': 100}
    mock_obtener_stock_disponible.return_value = 10  # <-- devolver stock suficiente
    mock_actualizar_stock.return_value = (True, "Stock actualizado")
    mock_guardar_compra.return_value = (True, "Compra registrada correctamente")

    # Simular POST con acción "comprar"
    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '0',
        'cantidad_0': '2',
        'accion': 'comprar'
    }, follow_redirects=True)

    # Parsear el HTML con BeautifulSoup
    soup = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    mensajes = [div.get_text(strip=True) for div in soup.find_all('div', class_='alert')]

    # Validaciones
    assert response.status_code == 200
    assert "Compra realizada con éxito. Stock actualizado." in mensajes



@patch('app_web.views_usuario.Carrito.obtener_todos_por_usuario')
def test_ver_carrito(mock_obtener_carrito, client, session_user):
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

    response = client.get('/ver_carrito')
    texto = response.data.decode('utf-8')

    assert response.status_code == 200
    assert 'Producto Test' in texto

@patch('app_web.views_usuario.Carrito.procesar_pago')
def test_pagar_carrito(mock_procesar_pago, client, session_user):
    mock_procesar_pago.return_value = (True, "Pago exitoso")

    response = client.post('/pagar_carrito', follow_redirects=True)
    texto = response.data.decode('utf-8')

    assert response.status_code == 200
    assert 'Pago exitoso' in texto

@patch('app_web.views_usuario.Carrito.eliminar_producto')
def test_eliminar_del_carrito(mock_eliminar, client, session_user):
    mock_eliminar.return_value = None

    response = client.post('/eliminar_del_carrito', data={
        'producto_id': '1',
        'talla': 'M',
        'color': 'Rojo'
    }, follow_redirects=True)

    texto = response.data.decode('utf-8')
    assert response.status_code == 200
    assert 'Producto eliminado' in texto

@patch('app_web.views_usuario.Compra.obtener_compras_usuario')
def test_ver_compras(mock_obtener_compras, client, session_user):
    mock_obtener_compras.return_value = [{
        'fecha': datetime.now(),
        'nombre': 'Producto Comprado',
        'descripcion': 'Descripción',
        'talla': 'M',
        'color': 'Rojo',
        'cantidad': 1,
        'precio_original': 100.0,
        'precio_final': 90.0
    }]

    response = client.get('/ver_compras')
    texto = response.data.decode('utf-8')

    assert response.status_code == 200
    assert 'Producto Comprado' in texto

# -----------------------------------------------------------
# Casos de error
# -----------------------------------------------------------

@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
def test_agregar_carrito_cantidad_cero(
    mock_obtener_producto,
    mock_obtener_detalles,
    client,
    session_user
):
    mock_obtener_detalles.return_value = [('M', 'Rojo', 10)]
    mock_obtener_producto.return_value = {'id': 1, 'precio': 100}

    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '0',
        'cantidad_0': '0'
    }, follow_redirects=True)

    texto = response.data.decode('utf-8')
    assert response.status_code == 200
    assert 'La cantidad debe ser mayor a cero' in texto

def test_agregar_carrito_usuario_no_autenticado(client):
    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '0',
        'cantidad_0': '2'
    }, follow_redirects=True)

    texto = response.data.decode('utf-8')
    assert 'Acceso no autorizado' in texto

@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
def test_agregar_carrito_sin_detalle_seleccionado(
    mock_obtener_producto,
    mock_obtener_detalles,
    client,
    session_user
):
    mock_obtener_detalles.return_value = [('M', 'Rojo', 10)]
    mock_obtener_producto.return_value = {'id': 1, 'precio': 100}

    response = client.post('/agregar_carrito/1', data={}, follow_redirects=True)

    texto = response.data.decode('utf-8')
    assert response.status_code == 200
    assert 'Debes seleccionar una talla y color' in texto

@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
def test_agregar_carrito_con_indice_invalido(
    mock_obtener_producto,
    mock_obtener_detalles,
    client,
    session_user
):
    mock_obtener_detalles.return_value = [('M', 'Rojo', 5)]
    mock_obtener_producto.return_value = {'id': 1, 'precio': 100}

    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '5'
    }, follow_redirects=True)

    texto = response.data.decode('utf-8')
    assert response.status_code == 200
    assert 'Selecci' in texto  

@patch('app_web.views_usuario.Producto.obtener_stock_disponible')
@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
def test_agregar_carrito_stock_insuficiente(
    mock_obtener_producto,
    mock_obtener_detalles,
    mock_stock,
    client,
    session_user
):
    mock_obtener_detalles.return_value = [('M', 'Rojo', 10)]
    mock_obtener_producto.return_value = {'id': 1, 'precio': 100}
    mock_stock.return_value = 1

    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '0',
        'cantidad_0': '5'
    }, follow_redirects=True)

    texto = response.data.decode('utf-8')
    assert response.status_code == 200
    assert 'No hay suficiente stock' in texto

def test_ver_carrito_no_autenticado(client):
    response = client.get('/ver_carrito', follow_redirects=True)
    texto = response.data.decode('utf-8')
    assert 'Acceso no autorizado' in texto

@patch('app_web.views_usuario.Carrito.obtener_todos_por_usuario')
def test_ver_carrito_error(mock_obtener_carrito, client, session_user):
    mock_obtener_carrito.side_effect = Exception("Error en carrito")

    response = client.get('/ver_carrito', follow_redirects=True)
    texto = response.data.decode('utf-8')
    assert response.status_code == 200
    assert 'Error al cargar el carrito' in texto

@patch('app_web.views_usuario.Carrito.procesar_pago')
def test_pagar_carrito_fallido(mock_procesar_pago, client, session_user):
    mock_procesar_pago.return_value = (False, "Error en pago")

    response = client.post('/pagar_carrito', follow_redirects=True)
    texto = response.data.decode('utf-8')
    assert response.status_code == 200
    assert 'Error en pago' in texto

def test_ver_compras_no_autenticado(client):
    response = client.get('/ver_compras', follow_redirects=True)
    texto = response.data.decode('utf-8')
    assert 'Acceso no autorizado' in texto

# -----------------------------------------------------------
# Test parametrizado para precio del producto
# -----------------------------------------------------------

@pytest.mark.parametrize("producto_data, precio_esperado", [
    ({'id': 1, 'precio': 100}, 100.0),
    ({'id': 1}, 0.0),
    (None, 0.0),
    ({'id': 1, 'precio': '150'}, 150.0),
])
@patch('app_web.views_usuario.Compra.guardar_compra')
@patch('app_web.views_usuario.Producto.actualizar_stock')
@patch('app_web.views_usuario.Producto.obtener_stock_disponible')
@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
def test_agregar_carrito_precio(
    mock_obtener_producto,
    mock_obtener_detalles,
    mock_obtener_stock,
    mock_actualizar_stock,
    mock_guardar_compra,
    client,
    session_user,
    producto_data,
    precio_esperado
):
    mock_obtener_detalles.return_value = [('M', 'Rojo', 10)]
    mock_obtener_producto.return_value = producto_data
    mock_obtener_stock.return_value = 10
    mock_actualizar_stock.return_value = (True, "Stock actualizado")
    mock_guardar_compra.return_value = (True, "Éxito")

    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '0',
        'cantidad_0': '2',
        'accion': 'comprar'
    }, follow_redirects=True)

    texto = response.data.decode('utf-8')

    if producto_data and 'precio' in producto_data:
        assert 'Compra realizada con' in texto or 'Éxito' in texto or 'Compra exitosa' in texto
        mock_guardar_compra.assert_called()
        args, _ = mock_guardar_compra.call_args
        assert float(args[5]) == precio_esperado
    else:
       
        assert mock_guardar_compra.called
        args, _ = mock_guardar_compra.call_args
        assert float(args[5]) == 0.0



# -----------------------------------------------------------
# Tests específicos para mensajes flash
# -----------------------------------------------------------



@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
def test_flash_sin_detalle_seleccionado(
    mock_obtener_producto,
    mock_obtener_detalles,
    client,
    session_user
):
    mock_obtener_detalles.return_value = [('M', 'Rojo', 10)]
    mock_obtener_producto.return_value = {'id': 1, 'precio': 100}

    response = client.post('/agregar_carrito/1', data={}, follow_redirects=True)
    texto = response.data.decode('utf-8')
    
    assert 'Debes seleccionar una talla y color' in texto
    assert 'danger' in texto

@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
def test_flash_indice_detalle_invalido(
    mock_obtener_producto,
    mock_obtener_detalles,
    client,
    session_user
):
    mock_obtener_detalles.return_value = [('M', 'Rojo', 5)]
    mock_obtener_producto.return_value = {'id': 1, 'precio': 100}

    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '10'
    }, follow_redirects=True)

    texto = response.data.decode('utf-8')
    assert 'Selección inválida' in texto
    assert 'danger' in texto

@patch('app_web.views_usuario.Producto.obtener_stock_disponible')
@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
def test_flash_stock_insuficiente(
    mock_obtener_producto,
    mock_obtener_detalles,
    mock_stock,
    client,
    session_user
):
    mock_obtener_detalles.return_value = [('M', 'Rojo', 10)]
    mock_obtener_producto.return_value = {'id': 1, 'precio': 100}
    mock_stock.return_value = 2

    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '0',
        'cantidad_0': '5'
    }, follow_redirects=True)

    texto = response.data.decode('utf-8')
    assert 'No hay suficiente stock' in texto
    assert 'Disponible: 2' in texto
    assert 'danger' in texto



@patch('app_web.views_usuario.Carrito.agregar_producto')
@patch('app_web.views_usuario.Producto.obtener_stock_disponible')
@patch('app_web.views_usuario.Producto.obtener_detalles_por_id')
@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
def test_flash_agregar_carrito_exitoso(
    mock_obtener_producto,
    mock_obtener_detalles,
    mock_stock,
    mock_agregar,
    client,
    session_user
):
    mock_obtener_detalles.return_value = [('M', 'Rojo', 10)]
    mock_obtener_producto.return_value = {'id': 1, 'precio': 100}
    mock_stock.return_value = 10
    mock_agregar.return_value = (True, "Agregado")

    response = client.post('/agregar_carrito/1', data={
        'detalle_seleccionado': '0',
        'cantidad_0': '2'
    }, follow_redirects=True)

    texto = response.data.decode('utf-8')
    assert 'Producto agregado al carrito' in texto
    assert 'success' in texto

def test_flash_ver_carrito_no_autenticado(client):
    response = client.get('/ver_carrito', follow_redirects=True)
    texto = response.data.decode('utf-8')
    assert 'Acceso no autorizado' in texto
    assert 'alert-danger' in texto


@patch('app_web.views_usuario.Carrito.obtener_todos_por_usuario')
def test_flash_error_ver_carrito(mock_obtener_carrito, client, session_user):
    mock_obtener_carrito.side_effect = Exception("Error en carrito")
    
    response = client.get('/ver_carrito', follow_redirects=True)
    texto = response.data.decode('utf-8')
    assert 'Error al cargar el carrito' in texto
    assert 'danger' in texto

@patch('app_web.views_usuario.Carrito.procesar_pago')
def test_flash_pago_parcial(mock_procesar_pago, client, session_user):
    mock_procesar_pago.return_value = (False, "Pago parcial: algunos productos no tenían stock")
    
    response = client.post('/pagar_carrito', follow_redirects=True)
    texto = response.data.decode('utf-8')
    assert 'Pago parcial' in texto
    assert 'warning' in texto

@patch('app_web.views_usuario.Carrito.procesar_pago')
def test_flash_pago_fallido(mock_procesar_pago, client, session_user):
    mock_procesar_pago.return_value = (False, "Error en pago")
    
    response = client.post('/pagar_carrito', follow_redirects=True)
    texto = response.data.decode('utf-8')
    assert 'Error en pago' in texto
    assert 'danger' in texto

@patch('app_web.views_usuario.Carrito.eliminar_producto')
def test_flash_eliminar_carrito_exitoso(mock_eliminar, client, session_user):
    response = client.post('/eliminar_del_carrito', data={
        'producto_id': '1',
        'talla': 'M',
        'color': 'Rojo'
    }, follow_redirects=True)
    
    texto = response.data.decode('utf-8')
    assert 'Producto eliminado del carrito' in texto
    assert 'success' in texto

@patch('app_web.views_usuario.Carrito.eliminar_producto')
def test_flash_error_eliminar_carrito(mock_eliminar, client, session_user):
    mock_eliminar.side_effect = Exception("Error eliminando")
    
    response = client.post('/eliminar_del_carrito', data={
        'producto_id': '1',
        'talla': 'M',
        'color': 'Rojo'
    }, follow_redirects=True)
    
    texto = response.data.decode('utf-8')
    assert 'Error al eliminar producto del carrito' in texto
    assert 'danger' in texto

def test_flash_ver_compras_no_autenticado(client):
    response = client.get('/ver_compras', follow_redirects=True)
    texto = response.data.decode('utf-8')
    assert 'Acceso no autorizado' in texto
    assert 'alert-danger' in texto

@patch('app_web.views_usuario.Producto.obtener_producto_por_id')
@patch('app_web.views_usuario.render_template')
@patch('app_web.views_usuario.flash')
@patch('app_web.views_usuario.redirect')
@patch('app_web.views_usuario.url_for')
def test_ver_producto_usuario(
    mock_url_for,
    mock_redirect,
    mock_flash,
    mock_render_template,
    mock_obtener_producto,
    client,
    app
):
    
    mock_url_for.return_value = '/menu_usuario'

   
    with client.session_transaction() as sess:
        sess['rol'] = 2

    # Caso 1: Producto encontrado
    mock_obtener_producto.return_value = {'id': 1, 'nombre': 'Producto A', 'precio': 100}
    mock_render_template.return_value = "Rendered Template"

    response = client.get('/producto_usuario/1')
    mock_obtener_producto.assert_called_once_with(1)
    mock_render_template.assert_called_once_with('usuario/ver_producto_usuario.html', producto=mock_obtener_producto.return_value)
    assert response.data == b"Rendered Template"

    # Reset mocks para el siguiente caso
    mock_obtener_producto.reset_mock()
    mock_render_template.reset_mock()
    mock_flash.reset_mock()
    mock_redirect.reset_mock()

    # Caso 2: Producto no encontrado
    mock_obtener_producto.return_value = None
    mock_redirect.return_value = "redirected"

    response = client.get('/producto_usuario/2')
    mock_flash.assert_called_once_with("Producto no encontrado", "warning")
    mock_redirect.assert_called_once_with('/menu_usuario')
    # Verificación modificada:
    assert response.data == b"redirected"

    # Reset mocks para el siguiente caso
    mock_obtener_producto.reset_mock()
    mock_flash.reset_mock()
    mock_redirect.reset_mock()

    # Caso 3: Excepción al obtener producto
    def raise_exception(id):
        raise Exception("DB error")
    mock_obtener_producto.side_effect = raise_exception
    # Configurar mock_redirect para devolver una respuesta más realista
    from flask import Response
    mock_redirect.return_value = Response(response="redirected", status=302)

    response = client.get('/producto_usuario/3')
    mock_flash.assert_called_once()
    args, kwargs = mock_flash.call_args
    assert "Error al obtener el producto" in args[0]
    mock_redirect.assert_called_once_with('/menu_usuario')
    # Verificación modificada:
    assert response.status_code == 302
    assert response.data == b"redirected"
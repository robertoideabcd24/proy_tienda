
import pytest
from unittest.mock import patch, MagicMock
from app_web.models.usuario.compras import Compra
from app_web.models.admin.producto_admin import Producto
from app_web.models.admin.producto_admin import AltaProductoPrecioException
from app_web.models.usuario.carrito_usuario import Carrito
from decimal import Decimal

# Test obtener_compras_usuario 
@patch("app_web.models.usuario.compras.pgdb")
def test_obtener_compras_usuario_exito(mock_pgdb):
    cursor_mock = mock_pgdb.get_cursor.return_value.__enter__.return_value
    cursor_mock.fetchall.return_value = [
        ("2025-06-01", "Producto1", "Descripcion1", "M", "Rojo", 3, Decimal('100.0'), Decimal('90.0')),
        ("2025-05-30", "Producto2", "Descripcion2", "L", "Azul", 1, Decimal('50.0'), Decimal('50.0')),
    ]

    compras = Compra.obtener_compras_usuario(1)

    assert len(compras) == 2
    assert compras[0]['nombre'] == "Producto1"
    assert compras[0]['precio_original'] == 100.0
    assert compras[0]['precio_final'] == 90.0

# Test obtener_compras_usuario
@patch("app_web.models.usuario.compras.pgdb")
def test_obtener_compras_usuario_error(mock_pgdb):
    mock_pgdb.get_cursor.side_effect = Exception("DB error")

    compras = Compra.obtener_compras_usuario(1)
    assert compras == []

# Test guardar_compra 
@patch("app_web.models.usuario.compras.pgdb")
def test_guardar_compra_exito(mock_pgdb):
    cursor_mock = mock_pgdb.get_cursor.return_value.__enter__.return_value
    cursor_mock.fetchone.return_value = [123]

    # Cantidad 12 -> descuento 30%
    exito, mensaje = Compra.guardar_compra(1, 10, "M", "Rojo", 12, '100')
    assert exito is True
    assert "correctamente" in mensaje
    cursor_mock.execute.assert_called()

    # Cantidad 6 -> descuento 20%
    exito, _ = Compra.guardar_compra(1, 10, "M", "Rojo", 6, '100')
    assert exito is True

    # Cantidad 3 -> descuento 10%
    exito, _ = Compra.guardar_compra(1, 10, "M", "Rojo", 3, '100')
    assert exito is True

    # Cantidad 1 -> sin descuento
    exito, _ = Compra.guardar_compra(1, 10, "M", "Rojo", 1, '100')
    assert exito is True

# Test guardar_compra 
@patch("app_web.models.usuario.compras.pgdb")
def test_guardar_compra_error(mock_pgdb):
    mock_pgdb.get_cursor.side_effect = Exception("DB error")
    exito, mensaje = Compra.guardar_compra(1, 10, "M", "Rojo", 5, '100')
    assert exito is False
    assert "DB error" in mensaje

# Test eliminar_compras_usuario
@patch("app_web.models.usuario.compras.pgdb")
def test_eliminar_compras_usuario_exito(mock_pgdb):
    cursor_mock = mock_pgdb.get_cursor.return_value.__enter__.return_value
    Compra.eliminar_compras_usuario(1)
    assert cursor_mock.execute.call_count == 2

# Test eliminar_compras_usuario 
@patch("app_web.models.usuario.compras.pgdb")
def test_eliminar_compras_usuario_error(mock_pgdb):
    mock_pgdb.get_cursor.side_effect = Exception("DB error")
    # No raise, solo print, por eso no se espera excepción
    Compra.eliminar_compras_usuario(1)




@patch("app_web.models.usuario.carrito_usuario.pgdb")
@patch("app_web.models.usuario.carrito_usuario.Compra.guardar_compra")
@patch("app_web.models.usuario.carrito_usuario.Producto.obtener_stock_fisico")
@patch("app_web.models.usuario.carrito_usuario.Producto.actualizar_stock")
def test_procesar_pago_compra_parcial(mock_actualizar_stock, mock_obtener_stock_fisico, mock_guardar_compra, mock_pgdb):
    # Simular items en carrito: 2 productos
    cursor_mock = mock_pgdb.get_cursor.return_value.__enter__.return_value
    cursor_mock.fetchall.return_value = [
        (1, 101, "Producto1", "M", "Rojo", 5, Decimal('100.00')),
        (2, 102, "Producto2", "L", "Azul", 3, Decimal('50.00')),
    ]

    # Producto1 tiene stock suficiente
    mock_obtener_stock_fisico.side_effect = [5, 3]

    # Producto1 puede actualizar stock con éxito
    mock_actualizar_stock.side_effect = [(True, ""), (False, "Error actualizar stock")]

    # Producto1 guarda compra exitosamente, Producto2 falla
    mock_guardar_compra.side_effect = [(True, "Compra guardada"), (False, "Error guardando compra")]

    exito, mensaje = Carrito.procesar_pago(1)

    
    assert exito is False
    assert "Compra parcial realizada" in mensaje
    assert "Producto1" in mensaje or "Producto2" in mensaje 

   
    cursor_mock.execute.assert_any_call("DELETE FROM carrito WHERE id IN %s", ((1,),))




import pytest
from unittest.mock import patch
from app_web.models.usuario.carrito_usuario import Carrito

@patch("app_web.models.usuario.carrito_usuario.pgdb")
@patch("app_web.models.usuario.carrito_usuario.Producto")
def test_agregar_producto_nuevo(mock_producto, mock_pgdb):
    usuario_id = 1
    producto_id = 10
    talla = "M"
    color = "Rojo"
    cantidad = 2

    mock_producto.obtener_stock_disponible.return_value = 10
    mock_pgdb.get_cursor.return_value.__enter__.return_value.fetchone.return_value = None

    with patch.object(Carrito, "guardar") as mock_guardar:
        exito, mensaje = Carrito.agregar_producto(usuario_id, producto_id, talla, color, cantidad)

    assert exito is True
    assert mensaje == "Producto agregado al carrito"
    mock_guardar.assert_called()

@patch("app_web.models.usuario.carrito_usuario.pgdb")
@patch("app_web.models.usuario.carrito_usuario.Producto")
def test_agregar_producto_sin_stock(mock_producto, mock_pgdb):
    usuario_id = 1
    producto_id = 10
    talla = "L"
    color = "Azul"
    cantidad = 5

    mock_producto.obtener_stock_disponible.return_value = 2
    mock_pgdb.get_cursor.return_value.__enter__.return_value.fetchone.return_value = None

    exito, mensaje = Carrito.agregar_producto(usuario_id, producto_id, talla, color, cantidad)

    assert exito is False
    assert "No hay suficiente stock" in mensaje


@patch("app_web.models.usuario.carrito_usuario.pgdb")
def test_obtener_por_usuario_y_producto_existente(mock_pgdb):
    mock_pgdb.get_cursor.return_value.__enter__.return_value.fetchone.return_value = (
        1, 1, 10, "M", "Rojo", 3, "2025-06-01"
    )

    resultado = Carrito.obtener_por_usuario_y_producto(1, 10, "M", "Rojo")
    assert resultado is not None
    assert resultado.id == 1
    assert resultado.usuario_id == 1
    assert resultado.talla == "M"

@patch("app_web.models.usuario.carrito_usuario.pgdb")
def test_obtener_por_usuario_y_producto_no_existente(mock_pgdb):
    mock_pgdb.get_cursor.return_value.__enter__.return_value.fetchone.return_value = None

    resultado = Carrito.obtener_por_usuario_y_producto(1, 10, "M", "Rojo")
    assert resultado is None


# 2. guardar - insertar y actualizar
@patch("app_web.models.usuario.carrito_usuario.pgdb")
def test_guardar_insertar(mock_pgdb):
    cursor = mock_pgdb.get_cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (5, "2025-06-01")

    carrito = Carrito(
        usuario_id=1, producto_id=10, talla="M", color="Rojo", cantidad=2
    )
    carrito.guardar()

    cursor.execute.assert_called()
    assert carrito.id == 5
    assert carrito.creado_en == "2025-06-01"

@patch("app_web.models.usuario.carrito_usuario.pgdb")
def test_guardar_actualizar(mock_pgdb):
    cursor = mock_pgdb.get_cursor.return_value.__enter__.return_value

    carrito = Carrito(
        id=5, usuario_id=1, producto_id=10, talla="M", color="Rojo", cantidad=4
    )
    carrito.guardar()

    cursor.execute.assert_called()


# 3. agregar_producto - existente incrementa cantidad
@patch("app_web.models.usuario.carrito_usuario.pgdb")
@patch("app_web.models.usuario.carrito_usuario.Producto")
def test_agregar_producto_existente_incrementa_cantidad(mock_producto, mock_pgdb):
    usuario_id = 1
    producto_id = 10
    talla = "M"
    color = "Rojo"
    cantidad = 2

    mock_producto.obtener_stock_disponible.return_value = 10

    mock_pgdb.get_cursor.return_value.__enter__.return_value.fetchone.return_value = (
        1, usuario_id, producto_id, talla, color, 3, "2025-06-01"
    )

    with patch.object(Carrito, "guardar") as mock_guardar:
        exito, mensaje = Carrito.agregar_producto(usuario_id, producto_id, talla, color, cantidad)

    assert exito is True
    assert mensaje == "Producto agregado al carrito"
    mock_guardar.assert_called()


# 4. obtener_todos_por_usuario
@patch("app_web.models.usuario.carrito_usuario.pgdb")
def test_obtener_todos_por_usuario(mock_pgdb):
    mock_pgdb.get_cursor.return_value.__enter__.return_value.fetchall.return_value = [
        (1, 10, "Producto1", "Descripcion1", 100.0, "M", "Rojo", 5, 10),
        (2, 11, "Producto2", "Descripcion2", 200.0, "L", "Azul", 3, 3),
    ]

    carrito = Carrito.obtener_todos_por_usuario(1)
    assert len(carrito) == 2
    assert carrito[0]['descuento_porcentaje'] == 10  # 5 unidades = 10%
    assert carrito[1]['descuento_porcentaje'] == 10  # 3 unidades = 10%


# 5. calcular_total
def test_calcular_total():
    carrito = [
        {'subtotal': 100},
        {'subtotal': 200},
        {'subtotal': 50},
    ]
    total = Carrito.calcular_total(carrito)
    assert total == 350


# 6. obtener_detalles_con_reserva
@patch("app_web.models.usuario.carrito_usuario.pgdb")
def test_obtener_detalles_con_reserva_correcto(mock_pgdb):
    cursor = mock_pgdb.get_cursor.return_value.__enter__.return_value
    cursor.fetchall.side_effect = [
        [("M", "Rojo", 10), ("L", "Azul", 5)],  # stock_detalles
        [("M", "Rojo", 2)]  # reservas
    ]

    resultado = Carrito.obtener_detalles_con_reserva(10, 1)
    assert resultado == [("M", "Rojo", 8), ("L", "Azul", 5)]

@patch("app_web.models.usuario.carrito_usuario.pgdb")
def test_obtener_detalles_con_reserva_error(mock_pgdb):
    mock_pgdb.get_cursor.side_effect = Exception("DB Error")

    resultado = Carrito.obtener_detalles_con_reserva(10, 1)
    assert resultado == []



@patch("app_web.models.usuario.carrito_usuario.pgdb")
@patch("app_web.models.usuario.carrito_usuario.Producto")
@patch("app_web.models.usuario.carrito_usuario.Compra")
def test_procesar_pago_exito(mock_compra, mock_producto, mock_pgdb):
    cursor = mock_pgdb.get_cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [
        (1, 10, "Prod1", "M", "Rojo", 2, 100.0)
    ]
    mock_producto.obtener_stock_fisico.return_value = 10
    mock_producto.actualizar_stock.return_value = (True, "OK")
    mock_compra.guardar_compra.return_value = (True, "Compra OK")

    exito, mensaje = Carrito.procesar_pago(1)
    assert exito is True
    assert "Compra realizada con éxito" in mensaje

@patch("app_web.models.usuario.carrito_usuario.pgdb")
@patch("app_web.models.usuario.carrito_usuario.Producto")
@patch("app_web.models.usuario.carrito_usuario.Compra")
def test_procesar_pago_parcial(mock_compra, mock_producto, mock_pgdb):
    cursor = mock_pgdb.get_cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [
        (1, 10, "Prod1", "M", "Rojo", 2, 100.0)
    ]
    mock_producto.obtener_stock_fisico.return_value = 1  # stock insuficiente

    exito, mensaje = Carrito.procesar_pago(1)
    assert exito is False
    assert ("No se pudo completar la compra" in mensaje) or ("Compra parcial realizada" in mensaje)

@patch("app_web.models.usuario.carrito_usuario.pgdb")
def test_procesar_pago_error_db(mock_pgdb):
    mock_pgdb.get_cursor.side_effect = Exception("DB error")
    exito, mensaje = Carrito.procesar_pago(1)
    assert exito is False
    assert "Error al procesar pago" in mensaje



@patch("app_web.models.usuario.carrito_usuario.pgdb")
def test_eliminar_producto_exito(mock_pgdb):
    cursor = mock_pgdb.get_cursor.return_value.__enter__.return_value
    Carrito.eliminar_producto(1, 10, "M", "Rojo")
    cursor.execute.assert_called()

@patch("app_web.models.usuario.carrito_usuario.pgdb")
def test_eliminar_producto_error(mock_pgdb):
    cursor = mock_pgdb.get_cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = Exception("Error eliminar")
    with pytest.raises(Exception):
        Carrito.eliminar_producto(1, 10, "M", "Rojo")



def test_calcular_descuento():
    assert Carrito.calcular_descuento(12) == 0.3
    assert Carrito.calcular_descuento(6) == 0.2
    assert Carrito.calcular_descuento(3) == 0.1
    assert Carrito.calcular_descuento(1) == 0.0

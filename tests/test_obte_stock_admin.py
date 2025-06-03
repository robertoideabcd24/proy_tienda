import pytest
from app_web.models.admin.producto_admin import Producto

@pytest.fixture
def producto_con_stock_y_reservas(setup_db):
    """Fixture que crea un producto con stock y reservas para pruebas"""
    # Crear producto de prueba
    producto_id = Producto.insertar_producto_en_db(
        nombre="Tenis con reservas",
        precio=150.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    # Agregar detalle con stock inicial
    talla = "9.5"
    color = "Negro"
    stock_fisico = 10
    Producto.insertar_detalle_producto(producto_id, talla, color, stock_fisico)
    
    
    with pgdb.get_cursor() as cursor:
        # Insertar reservas de prueba
        cursor.execute("""
            INSERT INTO carrito (usuario_id, producto_id, talla, color, cantidad, fecha_agregado)
            VALUES 
                (1, %s, %s, %s, 2, NOW()),
                (2, %s, %s, %s, 3, NOW())
        """, (producto_id, talla, color, producto_id, talla, color))
    
    yield {
        "producto_id": producto_id,
        "talla": talla,
        "color": color,
        "stock_fisico": stock_fisico,
        "reservas_esperadas": 5  # 2 + 3
    }
    
    # Limpieza después de la prueba
    with pgdb.get_cursor() as cursor:
        cursor.execute("DELETE FROM carrito WHERE producto_id = %s", (producto_id,))
    Producto.eliminar_producto(producto_id, 1)


def test_obtener_stock_disponible_detalle_no_existe():
    """Prueba cuando el detalle de producto no existe"""
    stock_disponible = Producto.obtener_stock_disponible(
        producto_id=99999,  # ID que no existe
        talla="10",
        color="Azul"
    )
    
    # Debería devolver 0 cuando no existe el detalle
    assert stock_disponible == 0

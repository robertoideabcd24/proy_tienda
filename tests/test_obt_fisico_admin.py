import pytest
from app_web.models.admin.producto_admin import Producto
from app_web.extension import pgdb

@pytest.fixture
def producto_con_stock(setup_db):
    """Fixture que crea un producto con stock físico para pruebas"""
    # Crear producto de prueba
    producto_id = Producto.insertar_producto_en_db(
        nombre="Tenis prueba stock físico",
        precio=120.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    # Agregar detalle con stock inicial
    talla = "7.5"
    color = "Azul"
    stock_inicial = 15
    Producto.insertar_detalle_producto(producto_id, talla, color, stock_inicial)
    
    yield {
        "producto_id": producto_id,
        "talla": talla,
        "color": color,
        "stock_inicial": stock_inicial
    }
    
    # Limpieza después de la prueba
    Producto.eliminar_producto(producto_id, 1)

def test_obtener_stock_fisico_no_existente():
    """Prueba obtener stock físico cuando el detalle no existe"""
    stock = Producto.obtener_stock_fisico(
        producto_id=99999,  # ID que no existe
        talla="10",
        color="Rojo"
    )
    
    # Debería devolver 0 cuando no existe el detalle
    assert stock == 0


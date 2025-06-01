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
    
    # Crear algunas reservas en carrito (simuladas)
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

# def test_obtener_stock_disponible_con_reservas(producto_con_stock_y_reservas):
#     """Prueba cálculo de stock disponible considerando reservas"""
#     # Datos del fixture
#     data = producto_con_stock_y_reservas
#     stock_esperado = data["stock_fisico"] - data["reservas_esperadas"]
    
#     # Ejecutar la función
#     stock_disponible = Producto.obtener_stock_disponible(
#         producto_id=data["producto_id"],
#         talla=data["talla"],
#         color=data["color"]
#     )
    
#     # Verificar resultado
#     assert stock_disponible == stock_esperado

# def test_obtener_stock_disponible_sin_reservas(setup_db):
#     """Prueba cuando no hay reservas en carritos"""
#     # Crear producto y detalle
#     producto_id = Producto.insertar_producto_en_db(
#         nombre="Tenis sin reservas",
#         precio=200.00,
#         disponible=True,
#         marca="Marca Test",
#         descripcion="Descripción test",
#         usuario_id=1
#     )
#     talla = "8"
#     color = "Blanco"
#     stock_fisico = 7
#     Producto.insertar_detalle_producto(producto_id, talla, color, stock_fisico)
    
#     try:
#         # Ejecutar la función
#         stock_disponible = Producto.obtener_stock_disponible(
#             producto_id=producto_id,
#             talla=talla,
#             color=color
#         )
        
#         # Verificar resultado (debería ser igual al stock físico)
#         assert stock_disponible == stock_fisico
    
#     finally:
#         # Limpieza
#         Producto.eliminar_producto(producto_id, 1)

def test_obtener_stock_disponible_detalle_no_existe():
    """Prueba cuando el detalle de producto no existe"""
    stock_disponible = Producto.obtener_stock_disponible(
        producto_id=99999,  # ID que no existe
        talla="10",
        color="Azul"
    )
    
    # Debería devolver 0 cuando no existe el detalle
    assert stock_disponible == 0

# def test_obtener_stock_disponible_mas_reservas_que_stock(producto_con_stock_y_reservas):
#     """Prueba cuando las reservas superan el stock físico (no debería ser negativo)"""
#     # Datos del fixture
#     data = producto_con_stock_y_reservas
    
#     # Agregar más reservas para superar el stock físico
#     with pgdb.get_cursor() as cursor:
#         cursor.execute("""
#             INSERT INTO carrito (usuario_id, producto_id, talla, color, cantidad, fecha_agregado)
#             VALUES (3, %s, %s, %s, %s, NOW())
#         """, (data["producto_id"], data["talla"], data["color"], data["stock_fisico"]))
    
#     # Ejecutar la función
#     stock_disponible = Producto.obtener_stock_disponible(
#         producto_id=data["producto_id"],
#         talla=data["talla"],
#         color=data["color"]
#     )
    
#     # Verificar que no sea negativo (debería ser 0)
#     assert stock_disponible == 0

# def test_obtener_stock_disponible_con_talla_numerica(setup_db):
#     """Prueba que funciona correctamente con tallas numéricas"""
#     # Crear producto con talla numérica
#     producto_id = Producto.insertar_producto_en_db(
#         nombre="Tenis talla numérica",
#         precio=180.00,
#         disponible=True,
#         marca="Marca Test",
#         descripcion="Descripción test",
#         usuario_id=1
#     )
#     talla = 9  # Talla como número
#     color = "Rojo"
#     stock_fisico = 4
#     Producto.insertar_detalle_producto(producto_id, talla, color, stock_fisico)
    
#     try:
#         # Ejecutar la función
#         stock_disponible = Producto.obtener_stock_disponible(
#             producto_id=producto_id,
#             talla=talla,
#             color=color
#         )
        
#         # Verificar resultado
#         assert stock_disponible == stock_fisico
    
#     finally:
#         # Limpieza
#         Producto.eliminar_producto(producto_id, 1)

# def test_obtener_stock_disponible_con_talla_decimal(setup_db):
#     """Prueba que funciona correctamente con tallas decimales como string"""
#     # Crear producto con talla decimal
#     producto_id = Producto.insertar_producto_en_db(
#         nombre="Tenis talla decimal",
#         precio=220.00,
#         disponible=True,
#         marca="Marca Test",
#         descripcion="Descripción test",
#         usuario_id=1
#     )
#     talla = "8.5"  # Talla decimal como string
#     color = "Verde"
#     stock_fisico = 6
#     Producto.insertar_detalle_producto(producto_id, talla, color, stock_fisico)
    
#     try:
#         # Ejecutar la función
#         stock_disponible = Producto.obtener_stock_disponible(
#             producto_id=producto_id,
#             talla=talla,
#             color=color
#         )
        
#         # Verificar resultado
#         assert stock_disponible == stock_fisico
    
#     finally:
#         # Limpieza
#         Producto.eliminar_producto(producto_id, 1)
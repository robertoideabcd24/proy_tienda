import pytest
from decimal import Decimal
from app_web.extension import pgdb
from app_web.models.admin.producto_admin import (
    Producto,
    AltaProductoDescripcionException,
    AltaProductoPrecioException,
    ProductoNoEncontradoException,
    AltaProductoException,
    ProductoDetalleException
)


@pytest.fixture(scope='module')
def setup_db():
    """Inicializa la conexión a la base de datos para las pruebas"""
    print("Configurando la base de datos de prueba...")
    yield pgdb
    print("Finalizando pruebas de base de datos...")


@pytest.mark.parametrize(
    "descripcion,precio",
    [("Tenis deportivos", 599.99), ("Zapatos casuales", 300.00)]
)
def test_crear_producto_valido(descripcion, precio):
    producto = Producto(descripcion=descripcion, precio=precio)
    assert producto.descripcion == descripcion
    assert producto.precio == precio


def test_crear_producto_precio_negativo():
    with pytest.raises(AltaProductoPrecioException):
        Producto(descripcion="Tenis deportivos", precio=-10)


def test_crear_producto_descripcion_vacia():
    with pytest.raises(AltaProductoDescripcionException):
        Producto(descripcion="", precio=599.99)


def test_insertar_producto(setup_db):
    nombre = "Tenis Nike Air"
    precio = Decimal('999.99')
    disponible = True
    marca = "Nike"
    descripcion = "Tenis deportivos de alta calidad"
    usuario_id = 1

    # Modificar la aserción para verificar que se devuelve un ID válido
    producto_id = Producto.insertar_producto_en_db(nombre, precio, disponible, marca, descripcion, usuario_id)
    assert isinstance(producto_id, int) and producto_id > 0

    producto_db = Producto.obtener_producto_por_id(producto_id)
    assert producto_db is not None
    assert producto_db['nombre'] == nombre
    assert float(producto_db['precio']) == float(precio)
    assert producto_db['marca'] == marca
    assert producto_db['descripcion'] == descripcion


def test_obtener_producto_por_id():
    producto_db = Producto.obtener_producto_por_id(1)
    assert producto_db is not None
    assert producto_db['id'] == 1


def test_producto_no_existente():
    with pytest.raises(ProductoNoEncontradoException):
        Producto.obtener_producto_por_id(9999)


def test_obtener_detalles_producto():
    producto_id = 1
    detalles = Producto.obtener_detalles_por_id(producto_id)
    assert detalles is not None
    assert len(detalles) > 0


@pytest.mark.parametrize("precio_input,precio_esperado", [
    ("999.99", 999.99),
    ("1500.00", 1500.00)
])
def test_precio_valido(precio_input, precio_esperado):
    try:
        precio_convertido = float(precio_input)
        assert precio_convertido == precio_esperado
    except ValueError:
        pytest.fail("Conversión inesperada de precio")


def test_precio_invalido():
    precio = "invalid_price"
    with pytest.raises(AltaProductoException, match="Error: el precio es inválido"):
        Producto(descripcion="Tenis deportivos", precio=precio)


def test_precio_demasiado_grande():
    precio = 10000000000  # mayor a 9999999999
    with pytest.raises(AltaProductoPrecioException, match="Error: el precio es demasiado grande"):
        Producto(descripcion="Tenis deportivos", precio=precio)


def test_consulta_prod_por_usuario():
    usuario_id = 1
    resultados = Producto.consulta_prod_por_usuario(usuario_id)
    assert resultados is not None
    assert isinstance(resultados, list)
    assert len(resultados) > 0
    for producto in resultados:
        assert 'id' in producto
        assert 'nombre' in producto
        assert 'precio' in producto


def test_consulta_prod_por_usuario_sin_resultados():
    with pytest.raises(ProductoNoEncontradoException, match="No se encontraron productos para este usuario"):
        Producto.consulta_prod_por_usuario(9999)


def test_insertar_detalle_producto_exitoso(setup_db):
    # Primero crear un nuevo producto para evitar conflictos
    nombre = "Producto prueba detalle"
    precio = Decimal('100.00')
    disponible = True
    marca = "Marca prueba"
    descripcion = "Descripción prueba"
    usuario_id = 1
    
    producto_id = Producto.insertar_producto_en_db(nombre, precio, disponible, marca, descripcion, usuario_id)
    
    # Insertar detalle con combinación única
    talla = "XL"  # Usar una talla diferente
    color = "Verde"  # Usar un color diferente
    cantidad = 5
    
    resultado = Producto.insertar_detalle_producto(producto_id, talla, color, cantidad)
    assert resultado is True
    
    # Verificar que el detalle se insertó correctamente
    detalles = Producto.obtener_detalles_por_id(producto_id)
    assert any(d for d in detalles if d[0] == talla and d[1] == color and d[2] == cantidad)


def test_insertar_detalle_producto_duplicado(setup_db):
    """Prueba que se lance excepción al insertar detalle duplicado"""
    # Creamos producto y detalle inicial
    producto_id = Producto.insertar_producto_en_db(
        "Producto duplicado", 200.00, True, "Marca prueba", "Descripción", 1
    )
    Producto.insertar_detalle_producto(producto_id, "L", "Azul", 5)
    
    # Intentamos insertar el mismo detalle nuevamente
    with pytest.raises(ProductoDetalleException) as exc_info:
        Producto.insertar_detalle_producto(producto_id, "L", "Azul", 5)
    
    assert "Ya existe un detalle con esta combinación" in str(exc_info.value)


def test_insertar_detalle_producto_no_existente(setup_db):
    """Prueba que se lance excepción cuando el producto no existe"""
    producto_id = 99999  # ID que no existe
    
    with pytest.raises(ProductoDetalleException) as exc_info:
        Producto.insertar_detalle_producto(producto_id, "S", "Blanco", 3)
    
    assert "El producto especificado no existe" in str(exc_info.value)

def test_insertar_detalle_producto_stock_invalido(setup_db):
    """Prueba que se lance excepción con stock inválido"""
    producto_id = Producto.insertar_producto_en_db(
        "Producto stock inválido", 300.00, True, "Marca prueba", "Descripción", 1
    )
    
    # Stock negativo
    with pytest.raises(ProductoDetalleException) as exc_info:
        Producto.insertar_detalle_producto(producto_id, "XL", "Rojo", -5)
    assert "Error al insertar detalle del producto" in str(exc_info.value)
    
    # Stock no numérico
    with pytest.raises(ProductoDetalleException) as exc_info:
        Producto.insertar_detalle_producto(producto_id, "XL", "Rojo", "no-numérico")
    assert "Error al insertar detalle del producto" in str(exc_info.value)


def test_consulta_prod_con_resultados(setup_db):
    """Prueba que la consulta devuelva resultados cuando hay productos"""
    # Insertamos algunos productos de prueba
    Producto.insertar_producto_en_db("Producto 1", 100.00, True, "Marca A", "Descripción 1", 1)
    Producto.insertar_producto_en_db("Producto 2", 200.00, False, "Marca B", "Descripción 2", 1)
    
    resultados = Producto.consulta_prod()
    
    assert isinstance(resultados, list)
    assert len(resultados) >= 2  # Puede haber más si la DB no está vacía
    
    # Verificamos la estructura de los resultados
    for producto in resultados:
        assert 'id' in producto
        assert isinstance(producto['id'], int)
        assert 'nombre' in producto
        assert 'precio' in producto
        assert 'disponible' in producto
        assert 'marca' in producto
        assert 'descripcion' in producto


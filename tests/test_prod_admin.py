from unittest.mock import MagicMock, patch
import pytest
from decimal import Decimal
from app_web.extension import pgdb
from app_web.models.admin.producto_admin import (
    Producto,
    AltaProductoDescripcionException,
    AltaProductoPrecioException,
    ProductoNoEncontradoException,
    AltaProductoException,
    ProductoDetalleException,
    DBException
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



def test_producto_no_existente():
    with pytest.raises(ProductoNoEncontradoException):
        Producto.obtener_producto_por_id(9999)


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


# por probar actualizar_producto

def test_actualizar_producto_exitoso(setup_db):
    """Prueba actualización exitosa de producto"""
    # Primero crear un producto de prueba
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto a actualizar",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        # Datos para actualización
        nuevos_datos = {
            "nombre": "Producto actualizado",
            "precio": 150.00,
            "disponible": False,
            "marca": "Nueva marca",
            "descripcion": "Nueva descripción"
        }
        
        # Actualizar el producto
        resultado = Producto.actualizar_producto(
            id=producto_id,
            **nuevos_datos
        )
        
        assert resultado is True
        
        # Verificar que los cambios se aplicaron
        producto_actualizado = Producto.obtener_producto_por_id(producto_id)
        assert producto_actualizado['nombre'] == nuevos_datos['nombre']
        assert float(producto_actualizado['precio']) == nuevos_datos['precio']
        assert producto_actualizado['disponible'] == nuevos_datos['disponible']
        assert producto_actualizado['marca'] == nuevos_datos['marca']
        assert producto_actualizado['descripcion'] == nuevos_datos['descripcion']
        
    finally:
        # Limpieza
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass


def test_actualizar_producto_no_pertenece_usuario(setup_db):
    """Prueba que no se puede actualizar producto de otro usuario"""
    # Crear producto con usuario 1
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto usuario 1",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        # Intentar actualizar con usuario 2 (que no es el dueño)
        with pytest.raises(ProductoNoEncontradoException) as exc_info:
            Producto.actualizar_producto(
                id=producto_id,
                nombre="Producto actualizado",
                precio=150.00,
                disponible=False,
                marca="Nueva marca",
                descripcion="Nueva descripción",
                usuario_id=2  # Usuario que no es el dueño
            )
        
        assert "Producto no encontrado o no pertenece al usuario" in str(exc_info.value)
        
    finally:
        # Limpieza
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass

#por probar eliminar_producto

def test_eliminar_producto_exitoso(setup_db):
    """Prueba eliminación exitosa de producto"""
    # Crear producto de prueba con detalles
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto a eliminar",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    # Agregar un detalle
    Producto.insertar_detalle_producto(producto_id, "M", "Azul", 10)

    try:
        # Eliminar el producto
        resultado = Producto.eliminar_producto(producto_id)
        assert resultado is True
        
        # Verificar que el producto ya no existe
        with pytest.raises(ProductoNoEncontradoException):
            Producto.obtener_producto_por_id(producto_id)
            
        # Verificar que los detalles también se eliminaron
        detalles = Producto.obtener_detalles_por_id(producto_id)
        assert detalles is None or len(detalles) == 0  # Maneja tanto None como lista vacía
            
    finally:
        # Limpieza por si falla la eliminación
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
                cursor.connection.commit()
        except:
            pass


def test_eliminar_producto_no_pertenece_usuario(setup_db):
    """Prueba que no se puede eliminar producto de otro usuario"""
    # Crear producto con usuario 1
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto usuario 1",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        # Intentar eliminar con usuario 2 (que no es el dueño)
        with pytest.raises(ProductoNoEncontradoException) as exc_info:
            Producto.eliminar_producto(producto_id, usuario_id=2)
        
        assert "Producto no encontrado o no pertenece al usuario" in str(exc_info.value)
        
    finally:
        # Limpieza
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass


def test_eliminar_producto_no_existente(setup_db):
    """Prueba eliminación de producto que no existe"""
    producto_id = 99999  # ID que no existe
    
    with pytest.raises(ProductoNoEncontradoException) as exc_info:
        Producto.eliminar_producto(producto_id)
    
    assert "No se pudo eliminar el producto" in str(exc_info.value)


# por probar
def test_eliminar_producto_error_generico(setup_db):
    """Prueba manejo de errores genéricos al eliminar producto"""
    # Use patch to simulate generic error
    with patch('app_web.models.admin.producto_admin.pgdb.get_cursor') as mock_cursor:
        # Configure the mock to raise a generic error
        mock_cursor.return_value.__enter__.return_value.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception) as exc_info:
            Producto.eliminar_producto(1)
        
        # Match the exact error message from the method
        assert "Error al eliminar el producto" in str(exc_info.value)

# tes para probar actualizar_detalle_producto


def test_actualizar_detalle_producto_no_existente(setup_db):
    """Prueba actualización de detalle que no existe"""
    detalle_id = 99999  # ID que no existe
    
    with pytest.raises(ProductoDetalleException) as exc_info:
        Producto.actualizar_detalle_producto(detalle_id, "M", "Azul", 10)
    
    # Match the actual error message from the method
    assert "Error al actualizar el detalle del producto" in str(exc_info.value)


def test_actualizar_detalle_producto_exitoso(setup_db):
    """Prueba actualización exitosa de detalle de producto"""
    # Crear producto y detalle de prueba
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba detalle",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    # Insertar detalle y obtener su ID
    Producto.insertar_detalle_producto(producto_id, "S", "Rojo", 5)
    detalles = Producto.obtener_detalles_completos_por_id(producto_id)
    detalle_id = detalles[0]['id']  # Acceder al ID correctamente

    try:
        # Actualizar el detalle
        resultado = Producto.actualizar_detalle_producto(detalle_id, "M", "Azul", 10)
        assert resultado is True
        
        # Verificar los cambios
        detalles_actualizados = Producto.obtener_detalles_completos_por_id(producto_id)
        detalle_actualizado = next(d for d in detalles_actualizados if d['id'] == detalle_id)
        assert detalle_actualizado['talla'] == "M"
        assert detalle_actualizado['color'] == "Azul"
        assert detalle_actualizado['stock'] == 10
        
    finally:
        # Limpieza
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass


def test_actualizar_detalle_producto_error_generico(setup_db, mocker):
    """Prueba manejo de errores genéricos al actualizar detalle"""
    # Mock para simular error en la base de datos
    mock_cursor = mocker.MagicMock()
    mock_cursor.__enter__.return_value.execute.side_effect = Exception("Error simulado")
    mocker.patch('app_web.models.admin.producto_admin.pgdb.get_cursor', return_value=mock_cursor)
    
    with pytest.raises(ProductoDetalleException) as exc_info:
        Producto.actualizar_detalle_producto(1, "M", "Azul", 10)
    
    assert "Error al actualizar el detalle del producto" in str(exc_info.value)

# no paso

def test_actualizar_detalle_producto_duplicado(setup_db):
    """Prueba actualización que genera duplicado"""
    # Crear producto y detalles de prueba
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba duplicado",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    # Insertar detalles iniciales
    Producto.insertar_detalle_producto(producto_id, "S", "Rojo", 5)
    Producto.insertar_detalle_producto(producto_id, "M", "Azul", 3)
    
    # Obtener IDs de los detalles
    detalles = Producto.obtener_detalles_completos_por_id(producto_id)
    detalle_a_actualizar = detalles[0]['id']  # Primer detalle (S, Rojo)
    detalle_existente = detalles[1]  # Segundo detalle (M, Azul)

    try:
        # Intentar actualizar el primer detalle para que coincida con el segundo
        with pytest.raises(ProductoDetalleException) as exc_info:
            Producto.actualizar_detalle_producto(
                detalle_a_actualizar,
                detalle_existente['talla'],  # M
                detalle_existente['color'],  # Azul
                5
            )
        
        assert "Ya existe un detalle con esta combinación" in str(exc_info.value)
        
    finally:
        # Limpieza
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass

# puebas para eliminar_detalle_producto

def test_eliminar_detalle_producto_exitoso(setup_db):
    """Prueba eliminación exitosa de detalle de producto"""
    # Crear producto y detalle de prueba
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba detalle",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    Producto.insertar_detalle_producto(producto_id, "S", "Rojo", 5)
    detalles = Producto.obtener_detalles_completos_por_id(producto_id)
    detalle_id = detalles[0]['id']

    try:
        # Eliminar el detalle
        resultado = Producto.eliminar_detalle_producto(detalle_id)
        assert resultado is True
        
        # Verificar que el detalle ya no existe
        detalles_restantes = Producto.obtener_detalles_completos_por_id(producto_id)
        assert len(detalles_restantes) == 0
        
    finally:
        # Limpieza
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass

def test_eliminar_detalle_producto_no_existente(setup_db):
    """Prueba eliminación de detalle que no existe"""
    detalle_id = 99999  # ID que no existe
    
    with pytest.raises(ProductoDetalleException) as exc_info:
        Producto.eliminar_detalle_producto(detalle_id)
    
    # Match the actual error message from the method
    assert "Error al eliminar el detalle del producto" in str(exc_info.value)

def test_eliminar_detalle_producto_error_generico(setup_db, mocker):
    """Prueba manejo de errores genéricos al eliminar detalle"""
    # Mock para simular error en la base de datos
    mock_cursor = mocker.MagicMock()
    mock_cursor.__enter__.return_value.execute.side_effect = Exception("Error simulado")
    mocker.patch('app_web.models.admin.producto_admin.pgdb.get_cursor', return_value=mock_cursor)
    
    with pytest.raises(ProductoDetalleException) as exc_info:
        Producto.eliminar_detalle_producto(1)
    
    assert "Error al eliminar el detalle del producto" in str(exc_info.value)
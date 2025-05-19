import builtins
import pytest
from app_web.extension import pgdb
from app_web.models.admin.producto_admin import Producto, AltaProductoDescripcionException, AltaProductoPrecioException, ProductoNoEncontradoException, AltaProductoException
from decimal import Decimal
from unittest.mock import MagicMock
import psycopg2

#andamos trabajando sobre la clase del modelo Producto

@pytest.fixture(scope='module')
def setup_db():
    """Configuración de la base de datos para las pruebas"""
    # Aquí puedes inicializar tu conexión a la base de datos
    # Solo se ejecutará una vez para todas las pruebas
    print("Configurando la base de datos de prueba...")
    # pgdb.init_app(app)  # Si necesitas inicializar tu base de datos aquí
    yield pgdb  # Lo que sea devuelto es accesible en las pruebas
    print("Limpiando después de las pruebas...")
    # Limpiar la base de datos si es necesario después de todas las pruebas

# Test para crear un producto válido
def test_crear_producto_valido():
    producto = Producto(descripcion="Tenis deportivos", precio=599.99)
    assert producto.descripcion == "Tenis deportivos"
    assert producto.precio == 599.99

# Test para crear un producto con precio negativo
def test_crear_producto_precio_negativo():
    with pytest.raises(AltaProductoPrecioException):
        Producto(descripcion="Tenis deportivos", precio=-10)

# Test para crear un producto con descripción vacía
def test_crear_producto_descripcion_vacia():
    with pytest.raises(AltaProductoDescripcionException):
        Producto(descripcion="", precio=599.99)

# Test para insertar producto en la base de datos
def test_insertar_producto(setup_db):
    nombre = "Tenis Nike Air"
    precio = Decimal('999.99')  # Aseguramos que el precio es un Decimal
    disponible = True
    marca = "Nike"
    descripcion = "Tenis deportivos de alta calidad"
    usuario_id = 1  # Usa un id de usuario válido para la prueba

    resultado = Producto.insertar_producto_en_db(nombre, precio, disponible, marca, descripcion, usuario_id)
    assert resultado is True

    # Verificar que el producto se haya insertado correctamente
    producto_db = Producto.obtener_producto_por_id(4)  # Suponiendo que el ID insertado es 1
    assert producto_db is not None
    assert producto_db['nombre'] == nombre
    assert producto_db['precio'] == precio  # Comparación entre Decimal y Decimal
    assert producto_db['marca'] == marca
    assert producto_db['descripcion'] == descripcion


# Test para obtener producto por ID
def test_obtener_producto_por_id():
    producto_db = Producto.obtener_producto_por_id(1)  
    assert producto_db is not None
    assert producto_db['id'] == 1

# Test para obtener producto con ID que no existe
def test_producto_no_existente():
    with pytest.raises(ProductoNoEncontradoException):
        Producto.obtener_producto_por_id(9999)  


# Test para obtener detalles de producto
def test_obtener_detalles_producto():
    producto_id = 1  
    detalles = Producto.obtener_detalles_por_id(producto_id)
    assert detalles is not None
    assert len(detalles) > 0  

def test_precio_valido():
    precio = "999.99"  
    try:
        precio_convertido = float(precio)
        assert precio_convertido == 999.99  
    except ValueError:
        pytest.fail("La conversión del precio falló inesperadamente")


def test_precio_invalido():
    precio = "invalid_price"  
    with pytest.raises(AltaProductoException, match="Error: el precio es inválido"):
        # Crear una instancia de Producto, lo que debe levantar la excepción
        Producto(descripcion="Tenis deportivos", precio=precio)

def test_precio_demasiado_grande():
    precio = 10000000000  # Precio mayor que 9999999999
    with pytest.raises(AltaProductoPrecioException, match="Error: el precio es demasiado grande"):
        # Crear una instancia de Producto, lo que debe levantar la excepción
        Producto(descripcion="Tenis deportivos", precio=precio)

@pytest.fixture
def mock_pgdb_cursor():
    # Creamos un mock para la base de datos
    mock_cursor = MagicMock()
    # Definimos el comportamiento esperado para cursor.fetchall()
    mock_cursor.fetchall.return_value = [
        (1, "Tenis Nike Air", True, 999.99, "Nike", "Tenis deportivos de alta calidad"),
        (2, "Tenis Adidas", False, 1500.00, "Adidas", "Tenis deportivos de alta calidad")
    ]
    return mock_cursor

def test_obtener_productos_usuario_exitoso(mock_pgdb_cursor):
    # Mock de la conexión a la base de datos
    mock_pgdb = MagicMock()
    mock_pgdb.get_cursor.return_value.__enter__.return_value = mock_pgdb_cursor

    # Llamamos al método que queremos probar
    usuario_id = 1
    resultados = Producto.obtener_producto_por_id(usuario_id)
    print(resultados)  
    
    # Verificamos los resultados
    assert resultados['id'] == 1
    assert resultados['nombre'] == "Ozelia"
    assert resultados['disponible'] == True
    assert resultados['precio'] == Decimal('2600.00')
    assert resultados['marca'] == 'Adidas'
    assert resultados['descripcion'] == 'Tenis deportivo'

def test_consulta_prod_por_usuario_exitoso(monkeypatch, mock_pgdb_cursor):
    # Simulamos pgdb para que use el mock
    mock_pgdb = MagicMock()
    mock_pgdb.get_cursor.return_value.__enter__.return_value = mock_pgdb_cursor

    # Parcheamos la propiedad db del Producto para que devuelva el mock_pgdb
    monkeypatch.setattr('app_web.models.admin.producto_admin.pgdb', mock_pgdb)

    # Ejecutamos el método
    usuario_id = 1
    resultados = Producto.consulta_prod_por_usuario(usuario_id)

    # Validamos los resultados
    assert len(resultados) == 2
    assert resultados[0]['id'] == 1
    assert resultados[0]['nombre'] == "Tenis Nike Air"
    assert resultados[1]['marca'] == "Adidas"


def test_consulta_prod_por_usuario_sin_resultados(monkeypatch):
    # Simulamos un cursor que no devuelve filas
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []

    mock_pgdb = MagicMock()
    mock_pgdb.get_cursor.return_value.__enter__.return_value = mock_cursor

    monkeypatch.setattr('app_web.models.admin.producto_admin.pgdb', mock_pgdb)

    # Ahora esperamos que se lance la excepción
    with pytest.raises(ProductoNoEncontradoException, match="No se encontraron productos para este usuario"):
        Producto.consulta_prod_por_usuario(9999)

def test_consulta_prod_por_usuario_error_generico_con_raise(monkeypatch):
    def fake_cursor():
        raise Exception("Error simulado")

    mock_pgdb = MagicMock()
    mock_pgdb.get_cursor.side_effect = fake_cursor

    monkeypatch.setattr('app_web.models.admin.producto_admin.pgdb', mock_pgdb)

    with pytest.raises(Exception, match="Error simulado"):
        Producto.consulta_prod_por_usuario(123)


def test_insertar_producto_en_db_error_generico(monkeypatch, capfd):
    # Simulamos un cursor que lanza una excepción
    def fake_cursor():
        raise Exception("Error simulado de inserción")

    mock_pgdb = MagicMock()
    mock_pgdb.get_cursor.side_effect = fake_cursor

    # Patch del pgdb
    monkeypatch.setattr('app_web.models.admin.producto_admin.pgdb', mock_pgdb)

    # Ejecutamos el método
    resultado = Producto.insertar_producto_en_db("test", 10.0, True, "marcaX", "desc", 1)

    # Capturamos la salida de consola
    out, err = capfd.readouterr()

    assert resultado is False
    assert "Error al insertar producto en la base de datos:" in out
    assert "Error simulado de inserción" in out


def test_obtener_producto_por_id_exitoso(monkeypatch):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1, "Ozelia", True, Decimal("2600.00"), "Adidas", "Tenis deportivo")

    mock_pgdb = MagicMock()
    mock_pgdb.get_cursor.return_value.__enter__.return_value = mock_cursor

    monkeypatch.setattr("app_web.models.admin.producto_admin.pgdb", mock_pgdb)

    resultado = Producto.obtener_producto_por_id(1)

    assert resultado == {
        'id': 1,
        'nombre': "Ozelia",
        'disponible': True,
        'precio': Decimal("2600.00"),
        'marca': "Adidas",
        'descripcion': "Tenis deportivo",
    }

def test_obtener_producto_por_id_no_existente(monkeypatch):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None  # No hay resultado

    mock_pgdb = MagicMock()
    mock_pgdb.get_cursor.return_value.__enter__.return_value = mock_cursor

    monkeypatch.setattr("app_web.models.admin.producto_admin.pgdb", mock_pgdb)

    with pytest.raises(ProductoNoEncontradoException, match="Producto con ID 999 no encontrado"):
        Producto.obtener_producto_por_id(999)


def test_obtener_producto_por_id_error_generico(monkeypatch):
    def fake_cursor():
        raise Exception("Error simulado en DB")

    mock_pgdb = MagicMock()
    mock_pgdb.get_cursor.side_effect = fake_cursor

    monkeypatch.setattr("app_web.models.admin.producto_admin.pgdb", mock_pgdb)

    with pytest.raises(Exception, match="Error al obtener producto"):
        Producto.obtener_producto_por_id(1)


def test_insertar_detalle_producto_exitoso(monkeypatch):
    mock_cursor = MagicMock()
    mock_cursor.connection.commit.return_value = None

    mock_pgdb = MagicMock()
    mock_pgdb.get_cursor.return_value.__enter__.return_value = mock_cursor

    monkeypatch.setattr('app_web.models.admin.producto_admin.pgdb', mock_pgdb)

    resultado = Producto.insertar_detalle_producto(1, "M", "Negro", 10)
    assert resultado is True
    mock_cursor.execute.assert_called_once()
    mock_cursor.connection.commit.assert_called_once()

def test_insertar_detalle_producto_foreign_key_violation(monkeypatch, capfd):
    fake_exception = Exception("clave foránea")

    mock_pgdb = MagicMock()

    class FakeCursor:
        def __enter__(self): raise fake_exception
        def __exit__(self, exc_type, exc_val, exc_tb): pass

    mock_pgdb.get_cursor.return_value = FakeCursor()

    monkeypatch.setattr('app_web.models.admin.producto_admin.pgdb', mock_pgdb)
    monkeypatch.setattr('app_web.models.admin.producto_admin.psycopg2.errors.ForeignKeyViolation', Exception)

    resultado = Producto.insertar_detalle_producto(9999, "L", "Rojo", 5)
    out, _ = capfd.readouterr()

    assert resultado is False
    assert "Error: El producto no existe o tiene relación con otras tablas" in out



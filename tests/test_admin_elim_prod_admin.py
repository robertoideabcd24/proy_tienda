import pytest
from flask import session, get_flashed_messages, url_for
from app_web.models.admin.producto_admin import Producto, ProductoNoEncontradoException, ProductoDetalleException

@pytest.fixture
def admin_session(client):
    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 1  # Rol de administrador
        sess['usuario'] = 'admin_test'
    yield client

def test_eliminar_producto_exitoso(client, admin_session):
    """Prueba eliminación exitosa de un producto"""
    # Primero creamos un producto de prueba
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto a eliminar",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        # Realizamos la petición POST para eliminar
        response = client.post(f'/eliminar_producto/{producto_id}', follow_redirects=True)
        
        # Verificaciones
        assert response.status_code == 200
        assert b"Producto eliminado correctamente" in response.data
        
        # Verificar que el producto ya no existe
        with pytest.raises(ProductoNoEncontradoException):
            Producto.obtener_producto_por_id(producto_id)
    finally:
        # Limpieza por si falla la prueba
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass

def test_eliminar_producto_error_general(client, admin_session):
    """Prueba manejo de errores inesperados al eliminar"""
    # Crear producto de prueba
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto test error",
        precio=200.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        # Guardar método original
        original_method = Producto.eliminar_producto
        
        try:
            # Configurar para que falle
            def mock_eliminar(*args, **kwargs):
                raise Exception("Error simulado")
            
            Producto.eliminar_producto = mock_eliminar
            
            with client:
                response = client.post(f'/eliminar_producto/{producto_id}', follow_redirects=True)
                
                assert response.status_code == 200
                messages = get_flashed_messages(with_categories=True)
                assert len(messages) == 1
                assert messages[0][0] == 'danger'
                assert "Error al eliminar el producto" in messages[0][1]
        
        finally:
            # Restaurar método original
            Producto.eliminar_producto = original_method
    finally:
        # Limpiar producto de prueba
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass

def test_eliminar_producto_sin_permisos(client):
    """Prueba que usuarios no autorizados no puedan eliminar"""
    # Crear producto de prueba
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto test permisos",
        precio=250.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        # Usuario sin sesión
        with client:
            response = client.post(f'/eliminar_producto/{producto_id}', follow_redirects=True)
            
            assert response.status_code == 200
            assert b"Iniciar sesi\xc3\xb3n" in response.data
        
        # Usuario con rol incorrecto (rol 2 = usuario normal)
        with client.session_transaction() as sess:
            sess['rol'] = 2
            sess['usuario_id'] = 2
        
        with client:
            response = client.post(f'/eliminar_producto/{producto_id}', follow_redirects=True)
            
            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert "Acceso no autorizado" in messages[0][1]
    finally:
        # Limpiar producto de prueba
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass


#no pasa

def test_eliminar_producto_no_encontrado(client, admin_session):
    """Prueba eliminar producto que no existe"""
    producto_id = 99999  # ID que no existe
    
    with client:
        response = client.post(f'/eliminar_producto/{producto_id}', follow_redirects=True)
        
        assert response.status_code == 200
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0][0] == 'warning'
        assert "Producto no encontrado o no pertenece al usuario" in messages[0][1]

def test_eliminar_producto_con_detalles(client, admin_session):
    """Prueba eliminar producto con detalles asociados"""
    # Crear producto y detalle
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto con detalles",
        precio=150.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        # Insertar detalle
        Producto.insertar_detalle_producto(producto_id, "M", "Rojo", 5)
        
        # Guardar método original
        original_method = Producto.eliminar_producto
        
        try:
            # Configurar para que lance ProductoDetalleException
            def mock_eliminar(*args, **kwargs):
                raise ProductoDetalleException("No se puede eliminar, tiene detalles asociados")
            
            Producto.eliminar_producto = mock_eliminar
            
            with client:
                response = client.post(f'/eliminar_producto/{producto_id}', follow_redirects=True)
                
                assert response.status_code == 200
                messages = get_flashed_messages(with_categories=True)
                assert len(messages) == 1
                assert messages[0][0] == 'danger'  # Debería ser danger según tu código
                assert "No se puede eliminar, tiene detalles asociados" in messages[0][1]
        
        finally:
            # Restaurar método original
            Producto.eliminar_producto = original_method
    finally:
        # Limpieza
        try:
            # Eliminar detalle primero
            Producto.eliminar_detalle_producto(producto_id, "M", "Rojo")
            # Luego el producto
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass
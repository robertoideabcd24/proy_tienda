import pytest
from flask import session, get_flashed_messages, url_for
from app_web.models.admin.producto_admin import Producto, ProductoNoEncontradoException

@pytest.fixture
def user_session(client):
    """Fixture para simular sesión de usuario normal"""
    with client.session_transaction() as sess:
        sess['usuario_id'] = 2
        sess['rol'] = 2  # Rol de usuario normal
        sess['usuario'] = 'user_test'
    yield client

def test_comprar_producto_exitoso(client, user_session):
    """Prueba acceso exitoso a comprar producto"""
    # Primero creamos un producto de prueba
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto para comprar",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1  # Otro usuario lo creó
    )
    
    try:
        # Añadimos detalles al producto
        Producto.insertar_detalle_producto(producto_id, "M", "Azul", 10)
        
        with client:
            response = client.get(f'/comprar/{producto_id}')
            
            # Verificaciones
            assert response.status_code == 200
            assert b"Producto para comprar" in response.data
            assert b"Marca Test" in response.data
            assert b"Azul" in response.data  # Verificar que se muestran los detalles
    finally:
        # Limpieza
        try:
            Producto.eliminar_detalle_producto(producto_id, "M", "Azul")
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass


def test_comprar_producto_sin_detalles(client, user_session):
    """Prueba producto sin detalles"""
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto sin detalles",
        precio=50.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        with client:
            response = client.get(f'/comprar/{producto_id}')
            
            assert response.status_code == 200
            assert b"Producto sin detalles" in response.data
           
            assert b"No hay detalles disponibles" in response.data or \
                   b"Sin detalles" in response.data  
    finally:
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass



def test_comprar_producto_error_general(client, user_session):
    """Prueba error inesperado"""
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto test error",
        precio=75.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
      
        original_method = Producto.obtener_producto_por_id
        Producto.obtener_producto_por_id = lambda *args: (_ for _ in ()).throw(Exception("Error de prueba"))
        
        with client:
            response = client.get(f'/comprar/{producto_id}', follow_redirects=True)
            
            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert messages[0][0] == 'danger'
            assert "Error al obtener el producto" in messages[0][1]
            assert "Error de prueba" in messages[0][1]
            # Verificar redirección
            assert b"Lista de Productos" in response.data
    finally:
        # Restaurar método original
        Producto.obtener_producto_por_id = original_method
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass

def test_comprar_producto_sin_permisos(client):
    """Prueba acceso no autorizado"""
 
    with client:
        response = client.get('/comprar/1', follow_redirects=True)
        
        assert response.status_code == 200
        assert b"Iniciar sesi\xc3\xb3n" in response.data or \
               b"Lista de Productos" in response.data  

#no funciona

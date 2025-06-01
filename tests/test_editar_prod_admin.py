import pytest
from flask import session, get_flashed_messages, url_for, request
from app_web.models.admin.producto_admin import Producto, ProductoNoEncontradoException, ProductoDetalleException

@pytest.fixture
def admin_session(client):
    """Fixture para simular sesión de administrador"""
    with client.session_transaction() as sess:
        sess['usuario_id'] = 1
        sess['rol'] = 1  # Rol de administrador
        sess['usuario'] = 'admin_test'
    yield client

def test_editar_producto_get_success(client, admin_session):
    """Prueba acceso GET exitoso a editar producto"""
    # Crear producto de prueba
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        with client:
            response = client.get(f'/producto/{producto_id}')
            
            assert response.status_code == 200
            assert b"Producto prueba" in response.data
            assert b"Editar Producto" in response.data  # Ajustar según tu template
    finally:
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass


def test_editar_producto_post_update_success(client, admin_session):
    """Prueba actualización exitosa de producto"""
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto a actualizar",
        precio=50.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        with client:
            response = client.post(f'/producto/{producto_id}', data={
                'nombre': 'Producto actualizado',
                'precio': '75.00',
                'marca': 'Nueva marca',
                'descripcion': 'Nueva descripción',
                'disponible': 'on'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert messages[0][0] == 'success'
            assert "Producto actualizado correctamente" in messages[0][1]
            
            # Verificar que los cambios se aplicaron
            producto = Producto.obtener_producto_por_id(producto_id)
            assert producto['nombre'] == 'Producto actualizado'
            assert float(producto['precio']) == 75.00
    finally:
        try:
            Producto.eliminar_producto(producto_id, 1)
        except:
            pass


def test_editar_producto_get_not_found(client, admin_session):
    """Prueba GET con producto no existente"""
    producto_id = 99999
    
    with client:
        response = client.get(f'/producto/{producto_id}', follow_redirects=True)
        
        assert response.status_code == 200
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0][0] == 'danger'
        assert "Error al consultar producto" in messages[0][1]  # Mensaje exacto que muestra tu app
        assert b"Lista de Productos" in response.data

def test_editar_producto_post_add_detail_success(client, admin_session):
    """Prueba agregar detalle exitoso"""
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto con detalles",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        with client:
            response = client.post(f'/producto/{producto_id}', data={
                'talla': 'M',
                'color': 'Azul',
                'stock': '10',
                'detalle_id': ''
            }, follow_redirects=True)
            
            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert messages[0][0] == 'info'
            assert "Detalle agregado correctamente" in messages[0][1]
            
            # Verificación adaptada a tu estructura de datos
            detalles = Producto.obtener_detalles_completos_por_id(producto_id)
            assert detalles, "No se encontraron detalles"
            # Asumiendo que detalles es una lista de diccionarios o namedtuples
            assert any(
                (d.talla == 'M' and d.color == 'Azul' and d.stock == 10) if hasattr(d, 'talla')
                else (d['talla'] == 'M' and d['color'] == 'Azul' and d['stock'] == 10) if isinstance(d, dict)
                else False
                for d in detalles
            )
    finally:
        try:
            detalles = Producto.obtener_detalles_completos_por_id(producto_id)
            for d in detalles:
                Producto.eliminar_detalle_producto(d.id if hasattr(d, 'id') else d['id'])
            Producto.eliminar_producto(producto_id, 1)
        except Exception as e:
            print(f"Error en limpieza: {str(e)}")


def test_editar_producto_post_unauthorized(client):
    """Prueba acceso no autorizado"""
    with client:
        response = client.get('/producto/1', follow_redirects=True)
        
        assert response.status_code == 200
        assert b"Iniciar sesi\xc3\xb3n" in response.data
        
        messages = get_flashed_messages(with_categories=True)
        if messages:  # Más flexible según implementación
            assert "Acceso no autorizado" in messages[0][1] or \
                   "Debes iniciar sesión" in messages[0][1]

def test_editar_producto_post_update_detail_success(client, admin_session):
    """Prueba actualización de detalle existente"""
    # Crear producto y detalle
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    # Insertar detalle inicial
    Producto.insertar_detalle_producto(producto_id, "S", "Rojo", 5)
    detalles = Producto.obtener_detalles_completos_por_id(producto_id)
    detalle_id = detalles[0]['id'] if isinstance(detalles[0], dict) else detalles[0].id

    try:
        with client:
            # Datos para actualización
            data = {
                'detalle_id': str(detalle_id),
                'talla': 'M',
                'color': 'Azul',
                'stock': '10',
                'actualizar_detalle': '1'
            }
            
            # Realizar la petición
            response = client.post(f'/producto/{producto_id}', data=data, follow_redirects=True)
            
            # Verificaciones
            assert response.status_code == 200
            
            # Verificar mensaje flash (ajustar según comportamiento real)
            messages = get_flashed_messages(with_categories=True)
            if messages:  # Puede que no haya mensaje si fue exitoso
                if messages[0][0] == 'info':
                    assert "Detalle actualizado correctamente" in messages[0][1]
                else:
                    assert "Error al actualizar el detalle del producto" in messages[0][1]
            
            # Verificar cambios en la base de datos
            detalles_actualizados = Producto.obtener_detalles_completos_por_id(producto_id)
            assert detalles_actualizados, "No se encontraron detalles después de actualizar"
            
            # Verificación adaptada para diccionarios
            if isinstance(detalles_actualizados[0], dict):
                detalle_actualizado = detalles_actualizados[0]
                assert detalle_actualizado['talla'] == 'M'
                assert detalle_actualizado['color'] == 'Azul'
                assert detalle_actualizado['stock'] == 10
            else:  # Para objetos
                detalle_actualizado = detalles_actualizados[0]
                assert detalle_actualizado.talla == 'M'
                assert detalle_actualizado.color == 'Azul'
                assert detalle_actualizado.stock == 10
                
    finally:
        # Limpieza
        try:
            detalles = Producto.obtener_detalles_completos_por_id(producto_id)
            for d in detalles:
                if isinstance(d, dict):
                    Producto.eliminar_detalle_producto(d['id'])
                else:
                    Producto.eliminar_detalle_producto(d.id)
            Producto.eliminar_producto(producto_id, 1)
        except Exception as e:
            print(f"Error en limpieza: {str(e)}")

def test_editar_producto_post_update_detail_failure(client, admin_session):
    """Prueba error al actualizar detalle (ProductoDetalleException)"""
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba error",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    # Insertar detalle inválido para forzar error
    Producto.insertar_detalle_producto(producto_id, "S", "Rojo", 5)
    detalles = Producto.obtener_detalles_completos_por_id(producto_id)
    detalle_id = detalles[0]['id'] if isinstance(detalles[0], dict) else detalles[0].id

    try:
        # Mock manual de la excepción
        original_method = Producto.actualizar_detalle_producto
        Producto.actualizar_detalle_producto = lambda *args: (_ for _ in ()).throw(
            ProductoDetalleException("Talla no válida"))
        
        with client:
            response = client.post(f'/producto/{producto_id}', data={
                'detalle_id': str(detalle_id),
                'talla': 'INVALID',  # Talla inválida
                'color': 'Azul',
                'stock': '10',
                'actualizar_detalle': '1'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert messages[0][0] == 'danger'
            assert "Talla no válida" in messages[0][1]
    finally:
        # Restaurar método original
        Producto.actualizar_detalle_producto = original_method
        try:
            detalles = Producto.obtener_detalles_completos_por_id(producto_id)
            for d in detalles:
                Producto.eliminar_detalle_producto(d['id'] if isinstance(d, dict) else d.id)
            Producto.eliminar_producto(producto_id, 1)
        except Exception as e:
            print(f"Error en limpieza: {str(e)}")

def test_editar_producto_post_delete_detail_success(client, admin_session):
    """Prueba eliminación exitosa de detalle"""
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba eliminar",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    # Insertar detalle a eliminar
    Producto.insertar_detalle_producto(producto_id, "S", "Rojo", 5)
    detalles = Producto.obtener_detalles_completos_por_id(producto_id)
    detalle_id = detalles[0]['id'] if isinstance(detalles[0], dict) else detalles[0].id

    try:
        with client:
            response = client.post(f'/producto/{producto_id}', data={
                'eliminar_detalle': str(detalle_id)
            }, follow_redirects=True)
            
            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert messages[0][0] == 'info'
            assert "Detalle eliminado correctamente" in messages[0][1]
            
            # Verificar que ya no existe el detalle
            detalles = Producto.obtener_detalles_completos_por_id(producto_id)
            assert not any(
    (d['id'] == detalle_id if isinstance(d, dict) else d.id == detalle_id)
    for d in detalles
)
    finally:
        try:
            Producto.eliminar_producto(producto_id, 1)
        except Exception as e:
            print(f"Error en limpieza: {str(e)}")

def test_editar_producto_post_delete_detail_failure(client, admin_session):
    """Prueba error al eliminar detalle"""
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba error eliminar",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        # Mock manual de la excepción
        original_method = Producto.eliminar_detalle_producto
        Producto.eliminar_detalle_producto = lambda *args: (_ for _ in ()).throw(
            ProductoDetalleException("No se puede eliminar el detalle"))
        
        with client:
            response = client.post(f'/producto/{producto_id}', data={
                'eliminar_detalle': '999'  # ID inexistente
            }, follow_redirects=True)
            
            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert messages[0][0] == 'danger'
            assert "No se puede eliminar el detalle" in messages[0][1]
    finally:
        # Restaurar método original
        Producto.eliminar_detalle_producto = original_method
        try:
            Producto.eliminar_producto(producto_id, 1)
        except Exception as e:
            print(f"Error en limpieza: {str(e)}")

def test_editar_producto_post_update_product_failure(client, admin_session):
    """Prueba error al actualizar producto (ProductoNoEncontradoException)"""
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba error",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        # Mock manual de la excepción
        original_method = Producto.actualizar_producto

        # Función mock que lanza la excepción con los mismos parámetros que recibe
        def mock_actualizar_producto(id, nombre, precio, disponible, marca, descripcion, usuario_id):
            raise ProductoNoEncontradoException("Producto no existe")

        Producto.actualizar_producto = mock_actualizar_producto

        with client:
            response = client.post(f'/producto/{producto_id}', data={
                'nombre': 'Nuevo nombre',
                'precio': '150.00',
                'marca': 'Nueva marca',
                'descripcion': 'Nueva descripción',
                'disponible': 'on'
            }, follow_redirects=True)

            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert messages[0][0] == 'warning'  # Changed from 'danger' to 'warning'
            assert "Producto no existe" in messages[0][1]  # Also updated to match exact exception message
    finally:
        # Restaurar método original
        Producto.actualizar_producto = original_method
        try:
            Producto.eliminar_producto(producto_id, 1)
        except Exception as e:
            print(f"Error en limpieza: {str(e)}")

# por probar

def test_editar_producto_post_general_update_detail_exception(client, admin_session):
    """Prueba error genérico al actualizar detalle"""
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba error genérico",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    # Insertar detalle para actualizar
    Producto.insertar_detalle_producto(producto_id, "S", "Rojo", 5)
    detalles = Producto.obtener_detalles_completos_por_id(producto_id)
    detalle_id = detalles[0]['id'] if isinstance(detalles[0], dict) else detalles[0].id

    try:
        # Mock manual de la excepción
        original_method = Producto.actualizar_detalle_producto
        
        def mock_actualizar_detalle(*args, **kwargs):
            raise Exception("Error genérico en actualización")

        Producto.actualizar_detalle_producto = mock_actualizar_detalle
        
        with client:
            response = client.post(f'/producto/{producto_id}', data={
                'detalle_id': str(detalle_id),
                'talla': 'M',
                'color': 'Azul',
                'stock': '10'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert messages[0][0] == 'danger'
            assert "Error al actualizar detalle" in messages[0][1]
    finally:
        # Restaurar método original
        Producto.actualizar_detalle_producto = original_method
        try:
            detalles = Producto.obtener_detalles_completos_por_id(producto_id)
            for d in detalles:
                Producto.eliminar_detalle_producto(d['id'] if isinstance(d, dict) else d.id)
            Producto.eliminar_producto(producto_id, 1)
        except Exception as e:
            print(f"Error en limpieza: {str(e)}")

def test_editar_producto_post_general_delete_detail_exception(client, admin_session):
    """Prueba error genérico al eliminar detalle"""
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba error eliminar genérico",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    # Insertar detalle a eliminar
    Producto.insertar_detalle_producto(producto_id, "S", "Rojo", 5)
    detalles = Producto.obtener_detalles_completos_por_id(producto_id)
    detalle_id = detalles[0]['id'] if isinstance(detalles[0], dict) else detalles[0].id

    try:
        # Mock manual de la excepción
        original_method = Producto.eliminar_detalle_producto
        
        def mock_eliminar_detalle(*args, **kwargs):
            raise Exception("Error genérico en eliminación")

        Producto.eliminar_detalle_producto = mock_eliminar_detalle
        
        with client:
            response = client.post(f'/producto/{producto_id}', data={
                'eliminar_detalle': str(detalle_id)
            }, follow_redirects=True)
            
            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert messages[0][0] == 'danger'
            assert "Error al eliminar detalle" in messages[0][1]
    finally:
        # Restaurar método original
        Producto.eliminar_detalle_producto = original_method
        try:
            detalles = Producto.obtener_detalles_completos_por_id(producto_id)
            for d in detalles:
                Producto.eliminar_detalle_producto(d['id'] if isinstance(d, dict) else d.id)
            Producto.eliminar_producto(producto_id, 1)
        except Exception as e:
            print(f"Error en limpieza: {str(e)}")

def test_editar_producto_post_general_update_product_exception(client, admin_session):
    """Prueba error genérico al actualizar producto"""
    producto_id = Producto.insertar_producto_en_db(
        nombre="Producto prueba error genérico",
        precio=100.00,
        disponible=True,
        marca="Marca Test",
        descripcion="Descripción test",
        usuario_id=1
    )
    
    try:
        # Mock manual de la excepción
        original_method = Producto.actualizar_producto
        
        def mock_actualizar_producto(*args, **kwargs):
            raise Exception("Error genérico en actualización")

        Producto.actualizar_producto = mock_actualizar_producto
        
        with client:
            response = client.post(f'/producto/{producto_id}', data={
                'nombre': 'Nuevo nombre',
                'precio': '150.00',
                'marca': 'Nueva marca',
                'descripcion': 'Nueva descripción',
                'disponible': 'on'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert messages[0][0] == 'danger'
            assert "Error al actualizar producto" in messages[0][1]
    finally:
        # Restaurar método original
        Producto.actualizar_producto = original_method
        try:
            Producto.eliminar_producto(producto_id, 1)
        except Exception as e:
            print(f"Error en limpieza: {str(e)}")

def test_editar_producto_get_product_not_found(client, admin_session):
    """Prueba GET con producto no encontrado"""
    # Mock the obtener_producto_por_id method to return None
    original_method = Producto.obtener_producto_por_id
    
    def mock_obtener_producto(id):
        return None
    
    Producto.obtener_producto_por_id = mock_obtener_producto
    
    try:
        with client:
            # ID que no existe
            response = client.get('/producto/999999', follow_redirects=True)
            
            assert response.status_code == 200
            messages = get_flashed_messages(with_categories=True)
            assert len(messages) == 1
            assert messages[0][0] == 'warning'  # This matches the None check case
            assert "Producto no encontrado" in messages[0][1]
            assert b"Lista de Productos" in response.data
    finally:
        # Restore original method
        Producto.obtener_producto_por_id = original_method
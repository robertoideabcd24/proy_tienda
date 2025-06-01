import pytest
from unittest.mock import MagicMock, patch
from app_web.models.admin.producto_admin import Producto

class TestActualizarStock:
    """Clase para probar el método actualizar_stock"""
   
    
    @patch('app_web.models.admin.producto_admin.pgdb.get_cursor')
    def test_actualizar_stock_detalle_no_encontrado(self, mock_cursor):
        """Prueba cuando no se encuentra el detalle del producto"""
        # Configurar el mock para que no devuelva resultados
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = None
        
        # Ejecutar la función
        resultado, mensaje = Producto.actualizar_stock(
            producto_id=1,
            talla="10",
            color="Azul",
            cantidad_a_restar=5
        )
        
        # Verificar resultados
        assert resultado is False
        assert mensaje == "Detalle no encontrado"
    
    @patch('app_web.models.admin.producto_admin.pgdb.get_cursor')
    def test_actualizar_stock_insuficiente(self, mock_cursor):
        """Prueba cuando no hay suficiente stock"""
        # Configurar el mock para devolver un stock bajo (3 unidades)
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (3,)
        
        # Ejecutar la función intentando restar 5 unidades
        resultado, mensaje = Producto.actualizar_stock(
            producto_id=1,
            talla="10",
            color="Azul",
            cantidad_a_restar=5
        )
        
        # Verificar resultados
        assert resultado is False
        assert mensaje == "Stock insuficiente"
    
    @patch('app_web.models.admin.producto_admin.pgdb.get_cursor')
    def test_actualizar_stock_error_generico(self, mock_cursor):
        """Prueba manejo de errores genéricos"""
        # Configurar el mock para lanzar una excepción
        mock_cursor.return_value.__enter__.return_value.execute.side_effect = Exception("Error de base de datos")
        
        # Ejecutar la función
        resultado, mensaje = Producto.actualizar_stock(
            producto_id=1,
            talla="10",
            color="Azul",
            cantidad_a_restar=5
        )
        
        # Verificar resultados
        assert resultado is False
        assert "Error al actualizar stock: Error de base de datos" in mensaje
    
    @patch('app_web.models.admin.producto_admin.pgdb.get_cursor')
    def test_actualizar_stock_con_talla_numerica(self, mock_cursor):
        """Prueba que la función maneje correctamente tallas numéricas"""
        # Configurar el mock
        mock_cursor.return_value.__enter__.return_value.execute.return_value = None
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (10,)
        
        # Ejecutar con talla como número (sin comillas)
        resultado, mensaje = Producto.actualizar_stock(
            producto_id=1,
            talla=10,  # Talla como número
            color="Azul",
            cantidad_a_restar=2
        )
        
        # Verificar resultados
        assert resultado is True
        assert mensaje == "Stock actualizado"
        
        # Verificar que la talla se pasó correctamente (como número)
        args, kwargs = mock_cursor.return_value.__enter__.return_value.execute.call_args
        assert args[1][2] == 10  # talla en la posición 2 de los parámetros

    @patch('app_web.models.admin.producto_admin.pgdb.get_cursor')
    def test_actualizar_stock_con_talla_string(self, mock_cursor):
        """Prueba que la función maneje correctamente tallas como strings"""
        # Configurar el mock
        mock_cursor.return_value.__enter__.return_value.execute.return_value = None
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (10,)
        
        # Ejecutar con talla como string
        resultado, mensaje = Producto.actualizar_stock(
            producto_id=1,
            talla="10.5",  # Talla como string
            color="Azul",
            cantidad_a_restar=2
        )
        
        # Verificar resultados
        assert resultado is True
        assert mensaje == "Stock actualizado"
        
        # Verificar que la talla se pasó correctamente (como string)
        args, kwargs = mock_cursor.return_value.__enter__.return_value.execute.call_args
        assert args[1][2] == "10.5"  # talla en la posición 2 de los parámetros
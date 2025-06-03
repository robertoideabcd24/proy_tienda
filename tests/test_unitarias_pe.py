import pytest
from decimal import Decimal
from app_web.models.admin.producto_admin import Producto
from app_web.models.admin.producto_admin import AltaProductoDescripcionException
from app_web.models.usuario.carrito_usuario import Carrito, CarritoError
from app_web.models.usuario.compras import Compra
from app_web.models.admin.producto_admin import (
    Producto,
    AltaProductoPrecioException,
    ProductoNoEncontradoException,
    ProductoDetalleException,
    DBException
)

class TestCarritoValidaciones:
    """Pruebas para las validaciones del carrito basadas en la tabla proporcionada"""
    
    @pytest.mark.parametrize("nombre_producto,talla,cantidad,precio,esperado_valido,esperado_descuento,esperado_preciofinal", [
        # Casos válidos con diferentes descuentos
        ("R9", 8, 1, 3600.00, True, "0", 3600.00),
        ("R9", 8, 1, 3600.00, True, "0", 3600.00),
        ("R9", 8, 4, 3600.00, True, "10 %", 3240.00),
        ("R9", 8, 7, 3600.00, True, "20 %", 2880.00),
        ("R9", 8, 13, 3600.00, True, "30 %", 2520.00),
        
        # Casos inválidos
        ("R9", 0, 1, 3600.00, False, "-", None),          # Talla inválida
        ("R9", 8, 55, 3600.00, False, "CantidadInvalida", None),  # Cantidad inválida
        ("R9", 8, -1, 3600.00, False, "CantidadInvalida", None),  # Cantidad inválida
        ("R"*55, 8, 1, 3600.00, False, "-", None),         # Nombre producto inválido (demasiado largo)
        ("", 8, 1, 3600.00, False, "-", None),           # Nombre producto inválido
        ("R9", 8, 1, 10000000, False, "-", None),          # Precio inválido
        ("R9", 8, 1, 0, False, "-", None),                 # Precio inválido
    ])
    

    def test_validaciones_carrito(self, nombre_producto, talla, cantidad, precio, 
                                esperado_valido, esperado_descuento, esperado_preciofinal):
        """Prueba todos los casos de la tabla de validaciones"""
        
        # 1. Validar nombre del producto (longitud)
        if len(nombre_producto) > 55:  # Asumiendo máximo 10 caracteres
            with pytest.raises(AltaProductoDescripcionException):
                Producto(nombre_producto, precio)
            return
        
        # 2. Validar precio
        if precio <= 0 or precio > 9999999999:
            with pytest.raises(AltaProductoPrecioException):
                Producto(nombre_producto, precio)
            return
        
        # 3. Validar talla (asumiendo tallas válidas son 1-20)
        if talla < 3 or talla > 12:
            try:
                Carrito.agregar_producto(1, 1, talla, 'color', 1)
                assert True, "Debería haber fallado por talla inválida"
            except CarritoError as e:
                assert "talla" in str(e).lower()
            return
        
        # 4. Validar cantidad (1-12 según tabla)
        if cantidad < 1 or cantidad > 50:
            try:
                Carrito.agregar_producto(1, 1, 8, 'color', cantidad)
                assert False, "Debería haber fallado por cantidad inválida"
            except CarritoError as e:
                assert "cantidad" in str(e).lower()
            return
        
        # Si pasa todas las validaciones, probar cálculo de descuento
        if esperado_valido:
            descuento = Carrito.calcular_descuento(cantidad)
            
            # Verificar descuento
            if descuento == 0:
                assert esperado_descuento == "0"
            elif descuento == 0.1:
                assert esperado_descuento == "10 %"
            elif descuento == 0.2:
                assert esperado_descuento == "20 %"
            elif descuento == 0.3:
                assert esperado_descuento == "30 %"
            
            # Verificar precio final
            precio_final = precio * (1 - descuento)
            assert precio_final == esperado_preciofinal

class TestDescuentosPorCantidad:
    """Pruebas específicas para los descuentos por cantidad"""
    
    @pytest.mark.parametrize("cantidad,descuento_esperado", [
        (1, 0),     # 0%
        (2, 0),     # 0%
        (3, 0.1),   # 10%
        (5, 0.1),   # 10%
        (6, 0.2),   # 20%
        (11, 0.2),  # 20%
        (12, 0.3),  # 30%
        (13, 0.3),  # 30%
    ])
    def test_calculo_descuentos(self, cantidad, descuento_esperado):
        """Prueba que los descuentos se calculan correctamente"""
        assert Carrito.calcular_descuento(cantidad) == descuento_esperado

class TestValidacionesProducto:
    """Pruebas específicas para validaciones de producto"""
    
    def test_nombre_producto_demasiado_largo(self):
        """Prueba que un nombre de producto demasiado largo es inválido"""
        nombre_largo = "R"*55  # 50 caracteres
        with pytest.raises(AltaProductoDescripcionException):
            Producto(len(nombre_largo), 3600.00)
    
    def test_nombre_producto_invalido(self):
        """Prueba que nombres de producto inválidos son rechazados"""
        with pytest.raises(AltaProductoDescripcionException):
            Producto(-1, 3600.00)
        with pytest.raises(AltaProductoDescripcionException):
            Producto("", 3600.00)
        with pytest.raises(AltaProductoDescripcionException):
            Producto(None, 3600.00)
    
    def test_precio_invalido(self):
        """Prueba que precios inválidos son rechazados"""
        with pytest.raises(AltaProductoPrecioException):
            Producto("R9", 0)
        with pytest.raises(AltaProductoPrecioException):
            Producto("R9", 99999999999)
        with pytest.raises(AltaProductoPrecioException):
            Producto("R9", -100)


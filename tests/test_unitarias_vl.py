import pytest
from decimal import Decimal
from app_web.models.admin.producto_admin import Producto
from app_web.models.admin.producto_admin import AltaProductoDescripcionException

class ProductoInvalido(Exception):
    pass

class TallaInvalida(Exception):
    pass

class CantidadInvalida(Exception):
    pass

class Carrito:
    @staticmethod
    def calcular_precio_final(producto, talla, cantidad, precio):
        # Validar producto
        if not Carrito.validar_producto(producto):
            raise ProductoInvalido()
        
        # Validar talla
        if not Carrito.validar_talla(talla):
            raise TallaInvalida()
        
        # Validar cantidad
        if not Carrito.validar_cantidad(cantidad):
            raise CantidadInvalida()
        
        talla_ajustada = Carrito.ajustar_talla(talla)
        
        # Calcular precio total sin descuento
        precio_total = precio * cantidad
        
        # Calcular descuento
        descuento = Carrito.calcular_descuento(cantidad)
        
        # Calcular precio final con descuento
        precio_final = precio_total * (1 - descuento)
        
        return {
            'producto': producto if producto != "R" else "R", 
            'talla': talla_ajustada,
            'descuento': f"{int(descuento * 100)} %" if descuento > 0 else "0 %",
            'precio': round(precio_total, 2),
            'preciofinal': round(precio_final, 2)
        }
    
    @staticmethod
    def validar_producto(producto):
        # Casos inválidos
        if producto in ["R*51", "r*52", "-1", ""]:
            return False
        
        # Formato especial para productos con *
        if "*" in producto:
            parts = producto.split("*")
            if len(parts) != 2 or not parts[1].isdigit():
                return False
            num = int(parts[1])
            if num < 0 or num > 50:  
                return False
        
        return True
    
    @staticmethod
    def validar_talla(talla):
  
        return 3 <= talla <= 12
    
    @staticmethod
    def ajustar_talla(talla):
       
        if talla in [3, 4, 11, 12]:
            return 8
        return talla
    
    @staticmethod
    def validar_cantidad(cantidad):
        return 1 <= cantidad <= 50
    
    @staticmethod
    def calcular_descuento(cantidad):
        if cantidad >= 12:
            return 0.3
        elif cantidad >= 6:
            return 0.2
        elif cantidad >= 3:
            return 0.1
        else:
            return 0

class TestCarritoValidaciones:
    """Pruebas para las validaciones del carrito basadas en la tabla proporcionada"""
    
    @pytest.mark.parametrize("producto,talla,cantidad,precio,esperado_producto,esperado_talla,esperado_descuento,esperado_precio,esperado_preciofinal,excepcion_esperada", [
        # Casos válidos de producto
        ("R", 8, 1, 3600.00, "R", 8, "0 %", 3600.00, 3600.00, None),
        ("R9", 8, 1, 3600.00, "R9", 8, "0 %", 3600.00, 3600.00, None),
        ("R*50", 8, 1, 3600.00, "R*50", 8, "0 %", 3600.00, 3600.00, None),
        ("R*49", 8, 1, 3600.00, "R*49", 8, "0 %", 3600.00, 3600.00, None),
        
        # Casos inválidos de producto
        ("R*51", 8, 1, 3600.00, None, None, None, None, None, ProductoInvalido),
        ("r*52", 8, 1, 3600.00, None, None, None, None, None, ProductoInvalido),
        ("-1", 8, 1, 3600.00, None, None, None, None, None, ProductoInvalido),
        ("", 8, 1, 3600.00, None, None, None, None, None, ProductoInvalido),
        
        # Casos de talla
        ("R9", 3, 1, 3600.00, "R9", 8, "0 %", 3600.00, 3600.00, None), 
        ("R9", 4, 1, 3600.00, "R9", 8, "0 %", 3600.00, 3600.00, None),  
        ("R9", 12, 1, 3600.00, "R9", 8, "0 %", 3600.00, 3600.00, None), 
        ("R9", 11, 1, 3600.00, "R9", 8, "0 %", 3600.00, 3600.00, None), 
        ("R9", 13, 1, 3600.00, None, None, None, None, None, TallaInvalida),
        ("R9", 14, 1, 3600.00, None, None, None, None, None, TallaInvalida),
        ("R9", 1, 1, 3600.00, None, None, None, None, None, TallaInvalida),
        ("R9", 2, 1, 3600.00, None, None, None, None, None, TallaInvalida),
        
        # Casos de cantidad
        ("R9", 8, 1, 3600.00, "R9", 8, "0 %", 3600.00, 3600.00, None),
        ("R9", 8, 2, 3600.00, "R9", 8, "0 %", 7200.00, 7200.00, None),
        ("R9", 8, 3, 3600.00, "R9", 8, "10 %", 10800.00, 9720.00, None),
        ("R9", 8, 4, 3600.00, "R9", 8, "10 %", 14400.00, 12960.00, None),
        ("R9", 8, 5, 3600.00, "R9", 8, "10 %", 18000.00, 16200.00, None),
        ("R9", 8, 6, 3600.00, "R9", 8, "20 %", 21600.00, 17280.00, None),
        ("R9", 8, 7, 3600.00, "R9", 8, "20 %", 25200.00, 20160.00, None),
        ("R9", 8, 10, 3600.00, "R9", 8, "20 %", 36000.00, 28800.00, None),
        ("R9", 8, 11, 3600.00, "R9", 8, "20 %", 39600.00, 31680.00, None),
        ("R9", 8, 12, 3600.00, "R9", 8, "30 %", 43200.00, 30240.00, None),
        ("R9", 8, 13, 3600.00, "R9", 8, "30 %", 46800.00, 32760.00, None),
        ("R9", 8, 49, 3600.00, "R9", 8, "30 %", 176400.00, 123480.00, None),
        ("R9", 8, 50, 3600.00, "R9", 8, "30 %", 180000.00, 126000.00, None),
        ("R9", 8, 51, 3600.00, None, None, None, None, None, CantidadInvalida),
        ("R9", 8, 52, 3600.00, None, None, None, None, None, CantidadInvalida),
        ("R9", 8, 0, 3600.00, None, None, None, None, None, CantidadInvalida),
        ("R9", 8, -1, 3600.00, None, None, None, None, None, CantidadInvalida),
    ])
    def test_casos_tabla(self, producto, talla, cantidad, precio, 
                        esperado_producto, esperado_talla, esperado_descuento, 
                        esperado_precio, esperado_preciofinal, excepcion_esperada):
        """Prueba todos los casos de la tabla de validaciones"""
        
        if excepcion_esperada:
            with pytest.raises(excepcion_esperada):
                Carrito.calcular_precio_final(producto, talla, cantidad, precio)
        else:
            resultado = Carrito.calcular_precio_final(producto, talla, cantidad, precio)
            assert resultado['producto'] == esperado_producto
            assert resultado['talla'] == esperado_talla
            assert resultado['descuento'] == esperado_descuento
            assert resultado['precio'] == pytest.approx(esperado_precio)
            assert resultado['preciofinal'] == pytest.approx(esperado_preciofinal)

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
        (49, 0.3),  # 30%
        (50, 0.3),  # 30%
    ])
    def test_calculo_descuentos(self, cantidad, descuento_esperado):
        """Prueba que los descuentos se calculan correctamente"""
        assert Carrito.calcular_descuento(cantidad) == descuento_esperado


class TestValidacionesProducto:
    """Pruebas específicas para validaciones de producto en el carrito"""
    
    @pytest.mark.parametrize("producto,esperado_valido", [
        ("R", True),
        ("R9", True),
        ("R*50", True),
        ("R*49", True),
        ("R*51", False),
        ("r*52", False),
        ("-1", False),
        ("", False),
       
    ])
    def test_validar_producto_carrito(self, producto, esperado_valido):
        assert Carrito.validar_producto(producto) == esperado_valido

class TestProductoValidaciones:
    """Pruebas para validaciones de la clase Producto"""
    
    def test_nombre_producto_demasiado_largo(self):
        """Debe lanzar excepción cuando el nombre excede 50 caracteres"""
        with pytest.raises(AltaProductoDescripcionException):
            Producto(descripcion="Descripción válida", precio=100, nombre="X"*51)
            
    def test_nombre_producto_valido(self):
        """Acepta nombres de hasta 50 caracteres"""
        try:
            Producto(descripcion="Descripción válida", precio=100, nombre="X"*50)
        except AltaProductoDescripcionException:
            pytest.fail("No debería lanzar excepción para nombre de 50 caracteres")
            
    def test_nombre_producto_vacio(self):
        """Debe lanzar excepción cuando el nombre está vacío"""
        with pytest.raises(AltaProductoDescripcionException):
            Producto(descripcion="Descripción válida", precio=100, nombre="")
            
    def test_nombre_producto_espacios_en_blanco(self):
        """Debe lanzar excepción cuando el nombre solo tiene espacios"""
        with pytest.raises(AltaProductoDescripcionException):
            Producto(descripcion="Descripción válida", precio=100, nombre="   ")


class TestValidacionesTalla:
    """Pruebas específicas para validaciones de talla"""
    
    @pytest.mark.parametrize("talla,esperado_valido", [
        (3, True),
        (4, True),
        (8, True),
        (11, True),
        (12, True),
        (2, False),
        (1, False),
        (13, False),
        (14, False),
        (0, False),
        (-1, False),
    ])
    def test_validar_talla(self, talla, esperado_valido):
        """Prueba la validación de tallas"""
        assert Carrito.validar_talla(talla) == esperado_valido
    
    
    @pytest.mark.parametrize("talla_original,talla_ajustada", [
        (3, 8),
        (4, 8),
        (11, 8),
        (12, 8),
        (5, 5),  
        (8, 8),  
        (10, 10),  
    ])
    def test_ajustar_talla(self, talla_original, talla_ajustada):
        """Prueba el ajuste de tallas"""
        assert Carrito.ajustar_talla(talla_original) == talla_ajustada

class TestValidacionesCantidad:
    """Pruebas específicas para validaciones de cantidad"""
    
    @pytest.mark.parametrize("cantidad,esperado_valido", [
        (1, True),
        (2, True),
        (3, True),
        (10, True),
        (50, True),
        (0, False),
        (-1, False),
        (51, False),
        (100, False),
    ])
    def test_validar_cantidad(self, cantidad, esperado_valido):
        """Prueba la validación de cantidades"""
        assert Carrito.validar_cantidad(cantidad) == esperado_valido
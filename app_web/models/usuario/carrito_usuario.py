from ...extension import pgdb
from ..admin.producto_admin import Producto
from decimal import Decimal
from ..usuario.compras import Compra

class Carrito:
    @staticmethod
    def obtener_por_usuario_y_producto(usuario_id, producto_id, talla, color):
        with pgdb.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, usuario_id, producto_id, talla, color, cantidad, creado_en
                FROM carrito
                WHERE usuario_id = %s AND producto_id = %s AND talla = %s AND color = %s
            """, (usuario_id, producto_id, talla, color))
            item = cursor.fetchone()
            
            if item:
                return Carrito(
                    id=item[0],
                    usuario_id=item[1],
                    producto_id=item[2],
                    talla=item[3],
                    color=item[4],
                    cantidad=item[5],
                    creado_en=item[6]  # ← Esto resuelve el error
                )
        return None

    def __init__(self, id=None, usuario_id=None, producto_id=None, talla=None, color=None, cantidad=None, creado_en=None):
        self.id = id
        self.usuario_id = usuario_id
        self.producto_id = producto_id
        self.talla = talla
        self.color = color
        self.cantidad = cantidad
        self.creado_en = creado_en

    def guardar(self):
        with pgdb.get_cursor() as cursor:
            if self.id:
                # Actualizar
                cursor.execute("""
                    UPDATE carrito
                    SET cantidad = %s
                    WHERE id = %s
                """, (self.cantidad, self.id))
            else:
                # Insertar nuevo y obtener también creado_en
                cursor.execute("""
                    INSERT INTO carrito
                    (usuario_id, producto_id, talla, color, cantidad)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, creado_en
                """, (self.usuario_id, self.producto_id, self.talla, self.color, self.cantidad))
                resultado = cursor.fetchone()
                self.id = resultado[0]
                self.creado_en = resultado[1]
    @staticmethod
    def agregar_producto(usuario_id, producto_id, talla, color, cantidad):
        item = Carrito.obtener_por_usuario_y_producto(usuario_id, producto_id, talla, color)
        if item:
            item.cantidad += cantidad
            item.guardar()
        else:
            nuevo_item = Carrito(
                usuario_id=usuario_id,
                producto_id=producto_id,
                talla=talla,
                color=color,
                cantidad=cantidad
            )
            nuevo_item.guardar()
  
    
    # Agregar estos métodos a la clase Carrito

    @staticmethod
    def obtener_todos_por_usuario(usuario_id):
        with pgdb.get_cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.producto_id, p.nombre, p.descripcion, p.precio, 
                    c.talla, c.color, c.cantidad
                FROM carrito c
                JOIN productos p ON c.producto_id = p.id
                WHERE c.usuario_id = %s
            """, (usuario_id,))
            items = cursor.fetchall()
            
            carrito = []
            for item in items:
                precio = float(item[4])
                cantidad = item[7]
                descuento = Carrito.calcular_descuento(cantidad)
                precio_con_descuento = precio * (1 - descuento)
                subtotal = precio_con_descuento * cantidad
                
                carrito.append({
                    'id': item[0],
                    'producto_id': item[1],
                    'nombre': item[2],
                    'descripcion': item[3],
                    'precio_original': precio,
                    'precio_final': precio_con_descuento,
                    'descuento_porcentaje': int(descuento * 100),
                    'talla': item[5],
                    'color': item[6],
                    'cantidad': cantidad,
                    'subtotal': subtotal
                })
            return carrito


    @staticmethod
    def calcular_total(carrito):
        return sum(item['subtotal'] for item in carrito)
        

    @staticmethod
    def obtener_detalles_con_reserva(producto_id, usuario_id):
        query_stock = """
        SELECT talla, color, stock FROM producto_detalles WHERE producto_id = %s
        """
        query_carrito = """
        SELECT talla, color, SUM(cantidad) FROM carrito
        WHERE producto_id = %s GROUP BY talla, color
        """

        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute(query_stock, (producto_id,))
                stock_detalles = cursor.fetchall()

                cursor.execute(query_carrito, (producto_id,))
                reservas = cursor.fetchall()
                reservas_dict = {(t, c): q for t, c, q in reservas}

                # Restar reservas al stock
                resultado = []
                for talla, color, stock in stock_detalles:
                    reservado = reservas_dict.get((talla, color), 0)
                    stock_mostrado = stock - reservado
                    resultado.append((talla, color, max(0, stock_mostrado)))
                return resultado

        except Exception as e:
            print("Error al obtener detalles con reservas:", e)
            return []
        

    # carrito_usuario.py
    @staticmethod
    def procesar_pago(usuario_id):
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute("""
                    SELECT producto_id, talla, color, cantidad 
                    FROM carrito 
                    WHERE usuario_id = %s
                """, (usuario_id,))
                items = cursor.fetchall()

                for item in items:
                    producto_id, talla, color, cantidad = item

                    # Obtener precio original del producto
                    cursor.execute("""
                        SELECT precio FROM productos WHERE id = %s
                    """, (producto_id,))
                    precio_original = cursor.fetchone()[0]
                    precio_original = Decimal(precio_original)

                    # Verificar stock y actualizarlo
                    exito, mensaje = Producto.actualizar_stock(producto_id, talla, color, cantidad)
                    if not exito:
                        return False, f"{mensaje} para el producto ID {producto_id}, talla '{talla}', color '{color}'"

                    # Guardar compra (el descuento se calcula en guardar_compra)
                    exito_compra, mensaje_compra = Compra.guardar_compra(
                        usuario_id, producto_id, talla, color, cantidad, precio_original
                    )
                    if not exito_compra:
                        return False, f"Error al guardar compra: {mensaje_compra}"

                # Vaciar carrito
                cursor.execute("DELETE FROM carrito WHERE usuario_id = %s", (usuario_id,))
            return True, "Pago procesado correctamente"
        except Exception as e:
            return False, str(e)
        

    @staticmethod
    def eliminar_producto(usuario_id, producto_id, talla, color):
        try:
            with pgdb.get_cursor() as cursor:
                query = """
                    DELETE FROM carrito
                    WHERE usuario_id = %s AND producto_id = %s AND talla = %s AND color = %s
                """
                cursor.execute(query, (usuario_id, producto_id, talla, color))
        except Exception as e:
            raise Exception(f"No se pudo eliminar el producto: {str(e)}")

    @staticmethod
    def calcular_descuento(cantidad):
        if cantidad >= 12:
            return 0.3  # 30% de descuento
        elif cantidad >= 6:
            return 0.2  # 20% de descuento
        elif cantidad >= 3:
            return 0.1  # 10% de descuento
        return 0.0  # Sin descuento

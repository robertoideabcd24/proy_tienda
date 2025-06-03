from ...extension import pgdb
from ..admin.producto_admin import Producto
from decimal import Decimal
from ..usuario.compras import Compra

class CarritoError(Exception):
    pass

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
                    creado_en=item[6]  
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
        if cantidad <= 0 or cantidad > 12:
            raise CarritoError("Cantidad inválida. Debe ser entre 1 y 12.")
        try:
            # Primero verificar stock disponible considerando reservas
            stock_disponible = Producto.obtener_stock_disponible(producto_id, talla, color)
            
            # Obtener cantidad ya reservada en el carrito por este usuario
            cantidad_en_carrito = 0
            item_existente = Carrito.obtener_por_usuario_y_producto(usuario_id, producto_id, talla, color)
            if item_existente:
                cantidad_en_carrito = item_existente.cantidad
            
            # Calcular stock realmente disponible
            stock_real = stock_disponible - cantidad_en_carrito
            
            if cantidad > stock_real:
                raise Exception(f"No hay suficiente stock. Disponible: {stock_real}")
            
            # Si pasa la validación, agregar al carrito
            if item_existente:
                item_existente.cantidad += cantidad
                item_existente.guardar()
            else:
                nuevo_item = Carrito(
                    usuario_id=usuario_id,
                    producto_id=producto_id,
                    talla=talla,
                    color=color,
                    cantidad=cantidad
                )
                nuevo_item.guardar()
                
            return True, "Producto agregado al carrito"
            
        except Exception as e:
            return False, str(e)
  
    
    # Agregar estos métodos a la clase Carrito

    @staticmethod
    def obtener_todos_por_usuario(usuario_id):
        with pgdb.get_cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.producto_id, p.nombre, p.descripcion, p.precio, 
                    c.talla, c.color, c.cantidad, pd.stock
                FROM carrito c
                JOIN productos p ON c.producto_id = p.id
                JOIN producto_detalles pd ON c.producto_id = pd.producto_id 
                    AND c.talla = pd.talla AND c.color = pd.color
                WHERE c.usuario_id = %s
            """, (usuario_id,))
            items = cursor.fetchall()
            
            carrito = []
            for item in items:
                precio = float(item[4])
                cantidad = item[7]
                stock_disponible = item[8]
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
                    'stock_disponible': stock_disponible,
                    'subtotal': subtotal,
                    'puede_comprar': stock_disponible >= cantidad
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
                # Obtener todos los items del carrito con información completa
                cursor.execute("""
                    SELECT c.id, c.producto_id, p.nombre, c.talla, c.color, c.cantidad, p.precio
                    FROM carrito c
                    JOIN productos p ON c.producto_id = p.id
                    WHERE c.usuario_id = %s
                """, (usuario_id,))
                items = cursor.fetchall()

                productos_comprados = []
                productos_sin_stock = []
                total_compra = Decimal('0')

                for item in items:
                    item_id, producto_id, nombre, talla, color, cantidad, precio = item
                    
                    # Verificar stock físico real (ignorando reservas)
                    stock_fisico = Producto.obtener_stock_fisico(producto_id, talla, color)
                    
                    if stock_fisico >= cantidad:
                        # Actualizar stock
                        exito, mensaje = Producto.actualizar_stock(producto_id, talla, color, cantidad)
                        if not exito:
                            productos_sin_stock.append({
                                'nombre': nombre,
                                'talla': talla,
                                'color': color,
                                'error': mensaje
                            })
                            continue
                        
                        # Calcular precio con descuento
                        descuento = Carrito.calcular_descuento(cantidad)
                        precio_con_descuento = Decimal(str(precio)) * (Decimal('1') - Decimal(str(descuento)))
                        subtotal = precio_con_descuento * Decimal(str(cantidad))
                        total_compra += subtotal
                        
                        # Guardar compra
                        exito_compra, mensaje_compra = Compra.guardar_compra(
                            usuario_id, producto_id, talla, color, cantidad, precio
                        )
                        
                        if not exito_compra:
                            productos_sin_stock.append({
                                'nombre': nombre,
                                'talla': talla,
                                'color': color,
                                'error': mensaje_compra
                            })
                        else:
                            productos_comprados.append(item_id)
                    else:
                        productos_sin_stock.append({
                            'nombre': nombre,
                            'talla': talla,
                            'color': color,
                            'error': f"Stock insuficiente (disponible: {stock_fisico})"
                        })

                # Eliminar solo los productos comprados exitosamente
                if productos_comprados:
                    cursor.execute("DELETE FROM carrito WHERE id IN %s", (tuple(productos_comprados),))

                # Construir mensaje de resultado
                if productos_sin_stock and productos_comprados:
                    mensaje = "Compra parcial realizada. "
                    mensaje += f"Total comprado: ${total_compra:.2f}. "
                    mensaje += "Los siguientes productos no pudieron procesarse:\n"
                    for prod in productos_sin_stock:
                        mensaje += f"- {prod['nombre']} (Talla: {prod['talla']}, Color: {prod['color']}): {prod['error']}\n"
                    return False, mensaje  # False indica compra parcial
                elif productos_sin_stock and not productos_comprados:
                    mensaje = "No se pudo completar la compra. Problemas con los productos:\n"
                    for prod in productos_sin_stock:
                        mensaje += f"- {prod['nombre']} (Talla: {prod['talla']}, Color: {prod['color']}): {prod['error']}\n"
                    return False, mensaje
                else:
                    return True, f"Compra realizada con éxito. Total: ${total_compra:.2f}"

        except Exception as e:
            return False, f"Error al procesar pago: {str(e)}"
        

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
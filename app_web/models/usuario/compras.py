from ...extension import pgdb
from decimal import Decimal


class Compra:
    @staticmethod
    def obtener_compras_usuario(usuario_id):
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        co.fecha, 
                        p.nombre, 
                        p.descripcion,
                        dc.talla, 
                        dc.color, 
                        dc.cantidad, 
                        p.precio AS precio_original,
                        dc.precio AS precio_final
                    FROM compras co
                    JOIN detalle_compra dc ON co.id = dc.compra_id
                    JOIN productos p ON dc.producto_id = p.id
                    WHERE co.usuario_id = %s
                    ORDER BY co.fecha DESC
                """, (usuario_id,))
                resultados = cursor.fetchall()

                compras = []
                for row in resultados:
                    compras.append({
                        'fecha': row[0],
                        'nombre': row[1],
                        'descripcion': row[2],
                        'talla': row[3],
                        'color': row[4],
                        'cantidad': row[5],
                        'precio_original': float(row[6]),  # ← Agregado
                        'precio_final': float(row[7])
                    })
                return compras
        except Exception as e:
            print("Error al obtener compras del usuario:", e)
            return []


    @staticmethod
    def guardar_compra(usuario_id, producto_id, talla, color, cantidad, precio):
        try:
            # Calcular descuento
            descuento = Decimal('0.0')
            if cantidad >= 12:
                descuento = Decimal('0.3')
            elif cantidad >= 6:
                descuento = Decimal('0.2')
            elif cantidad >= 3:
                descuento = Decimal('0.1')

            precio = Decimal(precio)
            precio_con_descuento = precio * (Decimal('1.0') - descuento)

            with pgdb.get_cursor() as cursor:
                # Insertar en compras
                cursor.execute("""
                    INSERT INTO compras (usuario_id, fecha)
                    VALUES (%s, NOW())
                    RETURNING id
                """, (usuario_id,))
                compra_id = cursor.fetchone()[0]

                # Insertar en detalle_compra
                cursor.execute("""
                    INSERT INTO detalle_compra (compra_id, producto_id, talla, color, cantidad, precio)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (compra_id, producto_id, talla, color, cantidad, precio_con_descuento))

            return True, "Compra guardada correctamente"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def eliminar_compras_usuario(usuario_id):
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM detalle_compra
                    WHERE compra_id IN (SELECT id FROM compras WHERE usuario_id = %s)
                """, (usuario_id,))
                cursor.execute("""
                    DELETE FROM compras WHERE usuario_id = %s
                """, (usuario_id,))
        except Exception as e:
            print("Error eliminando compras:", e)    
from extension import pgdb  # tu instancia PostgresDB

class Carrito:
    def __init__(self, id=None, usuario_id=None, producto_id=None, cantidad=1):
        self.id = id
        self.usuario_id = usuario_id
        self.producto_id = producto_id
        self.cantidad = cantidad

    @classmethod
    def obtener_por_usuario_y_producto(cls, usuario_id, producto_id):
        sql = "SELECT id, usuario_id, producto_id, cantidad FROM carrito WHERE usuario_id = %s AND producto_id = %s"
        with pgdb.get_cursor() as cursor:
            cursor.execute(sql, (usuario_id, producto_id))
            row = cursor.fetchone()
        if row:
            return cls(id=row[0], usuario_id=row[1], producto_id=row[2], cantidad=row[3])
        else:
            return None

    def guardar(self):
        with pgdb.get_cursor() as cursor:
            if self.id is None:
                # Insertar nuevo registro
                sql = "INSERT INTO carrito (usuario_id, producto_id, cantidad) VALUES (%s, %s, %s) RETURNING id"
                cursor.execute(sql, (self.usuario_id, self.producto_id, self.cantidad))
                self.id = cursor.fetchone()[0]
            else:
                # Actualizar registro existente
                sql = "UPDATE carrito SET cantidad = %s WHERE id = %s"
                cursor.execute(sql, (self.cantidad, self.id))
        # No es necesario hacer commit explícito porque get_cursor() ya lo hace

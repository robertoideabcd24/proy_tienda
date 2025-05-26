from extension import pgdb
import psycopg2.errors

# Definición de excepciones 
class AltaProductoException(Exception): pass
class AltaProductoPrecioException(Exception): pass
class DBException(Exception): pass
class AltaProductoDescripcionException(Exception): pass
class ProductoNoEncontradoException(Exception): pass
class ProductoDetalleException(Exception): pass

class Producto:
    def __init__(self, descripcion=None, precio=None, id=None):
        if descripcion is None or not isinstance(descripcion, str) or descripcion.strip() == "":
            raise AltaProductoDescripcionException("Error: la descripción del producto no puede estar vacía o ser inválida")

        if isinstance(precio, str):
            try:
                precio = float(precio)
            except ValueError:
                raise AltaProductoException("Error: el precio es inválido")
        
        if precio <= 0:
            raise AltaProductoPrecioException("Error: el precio no puede ser negativo o cero")
        
        if precio > 9999999999:
            raise AltaProductoPrecioException("Error: el precio es demasiado grande")

        self.id = id
        self.descripcion = descripcion
        self.precio = precio

    @property
    def db(self):
        global pgdb
        if pgdb is None:
            raise DBException("La conexión a la base de datos no ha sido inicializada")
        return pgdb

    @staticmethod
    def consulta_prod_por_usuario(usuario_id):
        resultados = []
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute("SELECT id, nombre, disponible, precio, marca, descripcion FROM productos WHERE usuario_id = %s", (usuario_id,))
                filas = cursor.fetchall()
                if not filas:
                    raise ProductoNoEncontradoException("No se encontraron productos para este usuario")
                for fila in filas:
                    resultados.append({
                        'id': fila[0],
                        'nombre': fila[1],
                        'disponible': fila[2],
                        'precio': fila[3],
                        'marca': fila[4],
                        'descripcion': fila[5],
                    })
        except ProductoNoEncontradoException as e:
            raise ProductoNoEncontradoException("No se encontraron productos para este usuario")
        except Exception as e:
            raise e

        return resultados
    
    @staticmethod
    def insertar_producto_en_db(nombre, precio, disponible, marca, descripcion, usuario_id):
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO productos (nombre, precio, disponible, marca, descripcion, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (nombre, float(precio), disponible, marca, descripcion, usuario_id))
                cursor.connection.commit()
            return True
        except Exception as e:
            print("Error al insertar producto en la base de datos:", e)
            return False
        
    @staticmethod
    def obtener_producto_por_id(id):
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, nombre, disponible, precio, marca, descripcion 
                    FROM productos WHERE id = %s
                """, (id,))
                fila = cursor.fetchone()
                if fila:
                    return {
                        'id': fila[0],
                        'nombre': fila[1],
                        'disponible': fila[2],
                        'precio': fila[3],
                        'marca': fila[4],
                        'descripcion': fila[5],
                    }
                else:
                    raise ProductoNoEncontradoException(f"Producto con ID {id} no encontrado")
        except ProductoNoEncontradoException:
            raise
        except Exception as e:
            raise Exception("Error al obtener producto") from e


    @staticmethod
    def insertar_detalle_producto(producto_id, talla, color, stock):
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO producto_detalles (producto_id, talla, color, stock) VALUES (%s, %s, %s, %s)",
                    (producto_id, talla, color, int(stock))
                )
                cursor.connection.commit()
            return True
        except psycopg2.errors.ForeignKeyViolation as fk:
            print("Error: El producto no existe o tiene relación con otras tablas:", fk)
            return False
        except Exception as e:
            print("Error al insertar detalle del producto:", e)
            return False

    @staticmethod
    def obtener_detalles_por_id(producto_id):
        query = """
        SELECT talla, color, stock
        FROM producto_detalles
        WHERE producto_id = %s
        """
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute(query, (producto_id,))
                detalles = cursor.fetchall()  
                
            return detalles if detalles else None
        except Exception as e:
            print("Error al obtener detalles del producto:", e)
            return None

    @staticmethod
    def consulta_prod():
        resultados = []
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute("SELECT id, nombre, disponible, precio, marca, descripcion FROM productos")
                filas = cursor.fetchall()
                for fila in filas:
                    resultados.append({
                        'id': fila[0],
                        'nombre': fila[1],
                        'disponible': fila[2],
                        'precio': fila[3],
                        'marca': fila[4],
                        'descripcion': fila[5],
                    })
        except Exception as e:
            print("Error al consultar productos:", e)

        return resultados


#Modificar producto
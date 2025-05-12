from ...extension import pgdb
import psycopg2.errors
class AltaProductoException(Exception): pass
class AltaProductoPrecioException(Exception): pass
class DBException(Exception): pass

class Producto:
    def __init__(self, descripcion=None, precio=None, id=None):
        if isinstance(precio, str):
            try:
                precio = float(precio)
            except:
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
            print("Error al consultar productos del usuario:", e)

        return resultados


    @staticmethod
    def obtener_producto_por_id(id):
        try:#checar para usuario y rol
            with pgdb.get_cursor() as cursor:
                cursor.execute("SELECT id, nombre, disponible, precio, marca, descripcion FROM productos WHERE id = %s", (id,))
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
        except Exception as e:
            print("Error al obtener producto:", e)

        return None

    @staticmethod
    def insertar_producto_en_db(nombre, precio, disponible, marca, descripcion, usuario_id):
        try:
            with pgdb.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO productos (nombre, precio, disponible, marca, descripcion, usuario_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (nombre, float(precio), disponible, marca, descripcion, usuario_id)
                )
                producto_id = cursor.fetchone()[0]
                cursor.connection.commit()
                return producto_id
        except ValueError as ve:
            print("Error de valor (conversión de tipos):", ve)
            return None
        except psycopg2.errors.InsufficientPrivilege as ip:
            print("Error de privilegios en PostgreSQL:", ip)
            return None
        except Exception as e:
            print("Error general al insertar producto:", e)
            return None



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
        except Exception as e:
            print("Error al insertar detalle del producto:", e)
            return False

    @staticmethod
    def obtener_detalles_por_id(producto_id):
        # Consulta SQL para obtener todos los detalles del producto
        query = """
        SELECT talla, color, stock
        FROM producto_detalles
        WHERE producto_id = %s
        """
        try:
            # Obtén el cursor de la conexión gestionada por el pool
            with pgdb.get_cursor() as cursor:
                cursor.execute(query, (producto_id,))
                detalles = cursor.fetchall()  # Devuelve todos los registros
                
            # Si no hay detalles, retorna None
            return detalles if detalles else None
        except Exception as e:
            print("Error al obtener detalles del producto:", e)
            return None

#Modificar producto
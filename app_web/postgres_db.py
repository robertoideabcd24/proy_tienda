from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager

db_config = { "host" : "localhost",
                "database" : "sistema_tienda",
                "user" : "uacm",
                "password" : "uacm1"}

_tabla_productos = "CREATE TABLE productos (" \
                "id SERIAL PRIMARY KEY,"  \
                "nombre VARCHAR(100) NOT NULL,"   \
                "precio NUMERIC(10,2) NOT NULL,"   \
                "disponible BOOLEAN DEFAULT TRUE,"   \
                "stock INTEGER DEFAULT 0,"   \
                "creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP" \
                ");"

class PostgresDB:
    def __init__(self):
        self.app = None
        self.pool = None

    def init_app(self, app):
        self.app = app
        self.connect()

    def connect(self):
        self.pool = ThreadedConnectionPool(minconn=1, maxconn=30, **db_config)

    def create_all_tables(self):
        drop_productos ="DROP TABLE IF EXISTS Productos;"
        with self.get_cursor() as cur: 
            cur.execute(drop_productos)
            cur.execute(_tabla_productos)


# El decorador @contextmanager, se utiliza para crear administradores de contexto (context managers), 
# lo que facilita la gestión de recursos de manera más limpia y eficiente. 
# Se puede definir el comportamiento de entrada y salida del contexto dentro de una función, en lugar de tener que definir una clase con los métodos __enter__ y __exit__
    @contextmanager
    def get_cursor(self):
        if self.pool is None:
            self.connect()
        con = self.pool.getconn()
        try:
            yield con.cursor()
            con.commit()
        finally:
            self.pool.putconn(con)
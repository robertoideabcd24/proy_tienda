from flask import render_template, request, redirect, url_for, session, flash
from functools import wraps
from .models.admin.usuario_admin import Usuario, UsuarioException
from .models.admin.producto_admin import Producto, AltaProductoException, AltaProductoPrecioException, AltaProductoDescripcionException, ProductoNoEncontradoException,ProductoDetalleException
from .extension import pgdb
import os
from werkzeug.utils import secure_filename
from uuid import uuid4
import time
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 

def rol_requerido(rol_permitido):
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'rol' not in session or session['rol'] != rol_permitido:
                flash("Acceso no autorizado", "danger")
                return redirect(url_for('login_home'))
            return func(*args, **kwargs)
        return wrapper
    return decorador


def crear_directorio_imagenes():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        print(f"Directorio {UPLOAD_FOLDER} creado exitosamente")

# iamgenes de productos
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app_web', 'static', 'product_images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def guardar_imagen_producto(producto_id, file):
    try:
        print(f"[DEBUG] Iniciando guardado de imagen para producto {producto_id}")
        print(f"[DEBUG] UPLOAD_FOLDER: {UPLOAD_FOLDER}")
        
        # Crear directorio si no existe
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            print(f"[DEBUG] Directorio creado: {UPLOAD_FOLDER}")
        
        if file and file.filename:
            # Generar nombre único
            timestamp = str(int(time.time()))
            extension = file.filename.split('.')[-1].lower()
            filename = secure_filename(f"prod_{producto_id}_{timestamp}.{extension}")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            print(f"[DEBUG] Intentando guardar en: {filepath}")
            
            # Guardar el archivo
            file.save(filepath)
            print(f"[DEBUG] Archivo guardado en: {filepath}")
            
            # Verificar que el archivo existe
            if os.path.exists(filepath):
                print(f"[DEBUG] Archivo verificado existe: {filepath}")
                return filename  # Devuelve solo el nombre del archivo
            else:
                print("[DEBUG] Error: El archivo no se guardó correctamente")
                return None
        else:
            print("[DEBUG] No se recibió archivo o nombre vacío")
            return None
    except Exception as e:
        print(f"[ERROR] Al guardar imagen: {str(e)}")
        return None
    
def obtener_ruta_imagen(producto_id):
    upload_folder = os.path.join('app_web', 'static', 'product_images')
    if not os.path.exists(upload_folder):
        return None
    
    # Buscar cualquier imagen que comience con "prod_[ID]_"
    for filename in os.listdir(upload_folder):
        if filename.startswith(f"prod_{producto_id}_"):
            return filename
    return None

def obtener_imagen_producto(producto_id):
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            return None
            
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.startswith(f"prod_{producto_id}_"):
                print(f"[DEBUG] Imagen encontrada: {filename}")
                return filename
        print(f"[DEBUG] No se encontró imagen para producto {producto_id}")
        return None
    except Exception as e:
        print(f"[ERROR] Al buscar imagen: {str(e)}")
        return None

def eliminar_imagen_producto(producto_id):
    """Elimina la imagen asociada a un producto"""
    imagen = obtener_imagen_producto(producto_id)
    if imagen:
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, imagen))
            return True
        except:
            return False
    return False


def registrar_rutas(app):
    #----------------------------------------
    # Página de registro al sistema
    #----------------------------------------
    @app.route('/', methods=['GET', 'POST'])
    @app.route('/consulta_productos', methods=['GET', 'POST'])
    def consulta_productos():
            try:
                resultados = Producto.consulta_prod()
                return render_template("consultar_bien.html", datos=resultados)
            except ProductoNoEncontradoException as pne:
                flash(str(pne), "danger")
                return render_template("consultar_bien.html", datos=[])
            except Exception as e:
                flash(f"Error al consultar productos: {str(e)}", "danger")
                return render_template("consultar_bien.html", datos=[])


    @app.route('/login', methods=['GET', 'POST'])
    def login_home():
        if request.method == 'POST':
            username = request.form['usuario']
            password = request.form['contrasena']

            try:
                usuario = Usuario.verificar_usuario(username, password)
                if usuario:
                    session['usuario'] = usuario['nombre']
                    session['correo'] = usuario['correo']
                    session['rol'] = usuario['rol']
                    session['usuario_id'] = usuario['id']

                    if usuario['rol'] == 1:
                        return redirect(url_for('consulta_stock'))
                    elif usuario['rol'] == 2:
                        return redirect(url_for('consulta_productos'))
                    else:
                        flash("Rol no válido", 'danger')
                        return redirect(url_for('login_home'))
                else:
                    flash("Credenciales incorrectas", 'danger')
                    return redirect(url_for('login_home'))
            except UsuarioException as ue:
                flash(str(ue), 'danger')
                return redirect(url_for('login_home'))
            except Exception as e:
                flash(f"Error al intentar iniciar sesión: {str(e)}", 'danger')
                return redirect(url_for('login_home'))

        return render_template('login.html')

 
    #----------------------------------------
    # Página para insertar usuario
    #----------------------------------------
    @app.route('/insertar_usuario', methods=['GET', 'POST'])
    def insertar_usuario():
        if request.method == 'POST':
            nombre = request.form['nombre']
            fecha_nacimiento = request.form['fecha_nacimiento']
            rol = request.form['rol']
            correo = request.form['correo']
            contrasena = request.form['contrasena']

            try:
                exito = Usuario.insertar_usuario_en_db(nombre, fecha_nacimiento, rol, correo, contrasena)
                if exito:
                    flash("Usuario registrado correctamente.", "success")
                    return redirect(url_for('login_home'))
                else:
                    flash("No se pudo registrar el usuario por un error desconocido.", "danger")
            except UsuarioException as ue:
                flash(str(ue), "danger")
            except Exception as e:
                flash("Ocurrió un error inesperado al registrar el usuario.", "danger")

        return render_template('insertar_usuario.html')

    #----------------------------------------
    # Perfil del usuario
    #----------------------------------------
    @app.route('/perfil_usuario')
    def perfil_usuario():
        try:
            if 'usuario' in session:
                return render_template('admin/perfil.html', usuario=session['usuario'], correo=session['correo'])
            else:
                flash("Primero inicia sesión para ver tu perfil.", "warning")
                return redirect(url_for('login_home'))
        except Exception as e:
            flash(f"Error al cargar el perfil de usuario: {str(e)}", "danger")
            return redirect(url_for('login_home'))
        
    #----------------------------------------
    # Cerrar sesión
    #----------------------------------------
    @app.route('/logout', methods=['POST'])
    def logout():
        try:
            session.clear()
            flash("Has cerrado sesión exitosamente.", "info")
        except Exception as e:
            flash(f"Error al cerrar sesión: {str(e)}", "danger")
        return redirect(url_for('login_home'))

    
    #----------------------------------------
    # Página de la consulta de stock productos
    #----------------------------------------
    @app.route('/consulta_stock', methods=['GET', 'POST'])
    @rol_requerido(1)
    def consulta_stock():
        usuario_id = session.get('usuario_id')
       
        try:
            resultados = Producto.consulta_prod_por_usuario(usuario_id)

            # Adjuntar ruta de imagen si existe
            for producto in resultados:
                producto['imagen'] = obtener_imagen_producto(producto['id'])
                print(f"[DEBUG] Producto {producto['id']} - Imagen: {producto['imagen']}")

            return render_template("admin/consultar_prod_admin.html", datos=resultados)
        except ProductoNoEncontradoException as e:
            flash(str(e), "info")
            # Mostramos la página igual pero con datos vacíos y un mensaje
            return render_template("admin/consultar_prod_admin.html", datos=[])
        except Exception as e:
            flash(f"Error al consultar productos: {str(e)}", "danger")
            return render_template("admin/consultar_prod_admin.html", datos=[])

    #----------------------------------------
    # Detalle de la consulta de productos para editar
    #----------------------------------------
    @app.route('/producto/<int:id>', methods=['GET', 'POST'])
    @rol_requerido(1)
    def editar_producto(id):
        usuario_id = session.get('usuario_id')
        
        # Manejar actualización de detalles
        if request.method == 'POST' and 'talla' in request.form:
            try:
                detalle_id = request.form.get('detalle_id')
                talla = request.form['talla']
                color = request.form['color']
                stock = request.form['stock']
                imagen = request.files.get('imagen')

                if detalle_id:  # Actualización
                    Producto.actualizar_detalle_producto(detalle_id, talla, color, stock)
                    flash("Detalle actualizado correctamente", "info")
                    # Manejar la imagen
                    if imagen and imagen.filename:
                        if allowed_file(imagen.filename):
                            nombre_archivo = guardar_imagen_producto(producto['id'], imagen)
                            if nombre_archivo:
                                # Actualizar el producto con el nombre de la imagen si es necesario
                                flash("Producto e imagen guardados exitosamente", "success")
                            else:
                                flash("Producto guardado pero la imagen no se pudo guardar", "warning")
                        else:
                            flash("Formato de imagen no válido", "warning")
                else:  # Nuevo detalle
                    Producto.insertar_detalle_producto(id, talla, color, stock)
                    flash("Detalle agregado correctamente", "info")
                    
                return redirect(url_for('editar_producto', id=id))

            except ProductoDetalleException as e:
                flash(str(e), "danger")
            except Exception as e:
                print("Error al actualizar detalle:", e)
                flash("Error al actualizar detalle", "danger")
            return redirect(url_for('editar_producto', id=id))

        # Manejar eliminación de detalles
        if request.method == 'POST' and 'eliminar_detalle' in request.form:
            try:
                detalle_id = request.form['eliminar_detalle']
                Producto.eliminar_detalle_producto(detalle_id)
                flash("Detalle eliminado correctamente", "info")
            except ProductoDetalleException as e:
                flash(str(e), "danger")
            except Exception as e:
                print("Error al eliminar detalle:", e)
                flash("Error al eliminar detalle", "danger")
            return redirect(url_for('editar_producto', id=id))

        # Manejar actualización del producto principal
        if request.method == 'POST':
            try:
                nombre = request.form['nombre']
                precio = float(request.form['precio'])
                disponible = 'disponible' in request.form 
                marca = request.form['marca']
                descripcion = request.form['descripcion']
                imagen = request.files.get('imagen')
                eliminar_imagen = 'eliminar_imagen' in request.form

                # Manejo de la imagen
                if eliminar_imagen:
                    eliminar_imagen_producto(id)
                elif imagen:
                    # Eliminar imagen anterior si existe
                    eliminar_imagen_producto(id)
                    guardar_imagen_producto(id, imagen)

                Producto.actualizar_producto(
                    id=id,
                    nombre=nombre,
                    precio=precio,
                    disponible=disponible,
                    marca=marca,
                    descripcion=descripcion,
                    usuario_id=usuario_id
                )
                
                flash("Producto actualizado correctamente", "success")
                return redirect(url_for('editar_producto', id=id))

            except ProductoNoEncontradoException as e:
                flash(str(e), "warning")
            except Exception as e:
                print("Error al actualizar producto:", e)
                flash("Error al actualizar producto", "danger")
            return redirect(url_for('editar_producto', id=id))

        # Si es GET
        try:
            producto = Producto.obtener_producto_por_id(id)
            if producto is None:
                flash("Producto no encontrado", "warning")
                return redirect(url_for('consulta_stock'))
            
            detalles = Producto.obtener_detalles_completos_por_id(id)
            # Obtener imagen si existe
            imagen = obtener_imagen_producto(id)
            producto['imagen'] = imagen if imagen else None
            
        except Exception as e:
            print("Error al obtener producto:", e)
            flash("Error al consultar producto", "danger")
            return redirect(url_for('consulta_stock'))

        return render_template('admin/editar_prod_admin.html', 
                            producto=producto, 
                            detalles=detalles)


    #----------------------------------------
    # Eliminar producto
    #----------------------------------------
    @app.route('/eliminar_producto/<int:id>', methods=['POST'])
    @rol_requerido(1)
    def eliminar_producto(id):
        usuario_id = session.get('usuario_id')

        try:
            # Primero eliminamos la imagen asociada al producto
            eliminar_imagen_producto(id)
            Producto.eliminar_producto(id=id, usuario_id=usuario_id)
            flash("Producto eliminado correctamente", "success")
        except ProductoNoEncontradoException as e:
            flash(str(e), "warning")
        except ProductoDetalleException as e:
            flash(str(e), "danger")
        except Exception as e:
            print("Error al eliminar producto:", e)
            flash("Error al eliminar el producto", "danger")
        
        return redirect(url_for('consulta_stock'))
    
    #----------------------------------------
    # Detalle de la consulta de productos
    #----------------------------------------
    @app.route('/comprar/<int:id>')
    #@rol_requerido(2)
    def comprar_producto(id):
        try:
            producto = Producto.obtener_producto_por_id(id)
            if producto:
                detalles = Producto.obtener_detalles_por_id(id)
                return render_template('usuario/comprar_prod_usu.html', 
                                    producto=producto,
                                    detalles=detalles)
            else:
                flash("Producto no encontrado", "warning")
                return redirect(url_for('consulta_productos'))
        except Exception as e:
            flash(f"Error al obtener el producto: {str(e)}", "danger")
            return redirect(url_for('consulta_productos'))

    #----------------------------------------
    # Página para insertar producto
    #----------------------------------------
    @app.route('/insertar_producto', methods=['GET', 'POST'])
    @rol_requerido(1)
    def insertar_producto():
        usuario_id = session.get('usuario_id')

        if request.method == 'POST':
            try:
                nombre = request.form['nombre'].strip()
                precio_str = request.form['precio'].strip()
                disponible = 'disponible' in request.form
                marca = request.form['marca'].strip()
                descripcion = request.form['descripcion'].strip()
                imagen = request.files.get('imagen')

                # Validaciones (las que ya tenías)
                if not nombre:
                    raise AltaProductoException("El nombre no puede estar vacío")

                if not precio_str:
                    raise AltaProductoPrecioException("El precio no puede estar vacío")

                try:
                    precio = float(precio_str)
                except ValueError:
                    raise AltaProductoPrecioException("El precio debe ser un número")

                if precio < 0:
                    raise AltaProductoPrecioException("el precio no puede ser negativo")

                if not descripcion:
                    raise AltaProductoDescripcionException("la descripción no puede estar vacía")

                # Inserción del producto
                exito = Producto.insertar_producto_en_db(nombre, precio, disponible, marca, descripcion, usuario_id)
                

                if exito:
                    producto = Producto.obtener_producto_por_nombre(nombre)
                    if not producto:
                        flash("Producto insertado pero no se pudo recuperar", "warning")
                        return redirect(url_for('consulta_stock'))
                    
                    # Manejar la imagen
                    if imagen and imagen.filename:
                        if allowed_file(imagen.filename):
                            nombre_archivo = guardar_imagen_producto(producto['id'], imagen)
                            if nombre_archivo:
                                # Actualizar el producto con el nombre de la imagen si es necesario
                                flash("Producto e imagen guardados exitosamente", "success")
                            else:
                                flash("Producto guardado pero la imagen no se pudo guardar", "warning")
                        else:
                            flash("Formato de imagen no válido", "warning")
                    else:
                        flash("Producto guardado exitosamente", "success")
                    
                    return redirect(url_for('consulta_stock'))
                else:
                    flash("Ocurrió un error al insertar el producto.", "danger")
                    return redirect(url_for('insertar_producto'))

            except (AltaProductoException, AltaProductoPrecioException, AltaProductoDescripcionException) as e:
                flash(str(e), "warning")
                return redirect(url_for('insertar_producto'))

            except Exception as e:
                flash(f"Error inesperado: {str(e)}", "danger")
                return redirect(url_for('insertar_producto'))

        return render_template('admin/insertar_prod_admin.html')

    
    #----------------------------------------
    # Insertar detalles del producto
    #----------------------------------------
    @app.route('/insertar_detalles_producto/<int:producto_id>', methods=['GET', 'POST'])
    @rol_requerido(1)
    def insertar_detalles_producto(producto_id):
        usuario_id = session.get('usuario_id')
        
        try:
            if request.method == 'POST':
                talla = request.form['talla']
                color = request.form['color']
                stock = request.form['stock']
                imagen = request.files.get('imagen')
                eliminar_imagen = 'eliminar_imagen' in request.form

                # Manejo de la imagen
                if eliminar_imagen:
                    eliminar_imagen_producto(producto_id)
                elif imagen:
                    eliminar_imagen_producto(producto_id)
                    guardar_imagen_producto(producto_id, imagen)

                exito = Producto.insertar_detalle_producto(producto_id, talla, color, stock)
                if exito:
                    flash("Detalle del producto insertado correctamente.", "info")
                    return redirect(url_for('insertar_detalles_producto', producto_id=producto_id))
                else:
                    flash("Error al insertar detalles del producto.", "danger")

            producto = Producto.obtener_producto_por_id(producto_id)
            if not producto:
                flash("Producto no encontrado", "warning")
                return redirect(url_for('consulta_stock'))
            
            # Obtener imagen
            imagen = obtener_imagen_producto(producto_id)
            producto['imagen'] = imagen if imagen else None

            producto_detalles = Producto.obtener_detalles_por_id(producto_id)
            return render_template('admin/insertar_prod_det_admin.html', 
                       producto=producto, 
                       producto_detalles=producto_detalles)
        except Exception as e:
            flash(f"Ocurrió un error: {str(e)}", "danger")
            return redirect(url_for('consulta_stock'))

     #----------------------------------------
    # Página de la consulta de productos
    #----------------------------------------

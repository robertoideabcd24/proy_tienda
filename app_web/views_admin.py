from flask import render_template, request, redirect, url_for, session, flash
from functools import wraps
from .models.admin.usuario_admin import Usuario, UsuarioException
from .models.admin.producto_admin import Producto, AltaProductoException, AltaProductoPrecioException, AltaProductoDescripcionException

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

def registrar_rutas(app):
    #----------------------------------------
    # Página de registro al sistema
    #----------------------------------------
    @app.route('/', methods=['GET', 'POST'])
    @app.route('/consulta_productos', methods=['GET', 'POST'])
    def consulta_productos():
            resultados = Producto.consulta_prod()
            return render_template("consultar_bien.html", datos=resultados)


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
                        return redirect(url_for('menu_admin'))
                    elif usuario['rol'] == 2:
                        return redirect(url_for('menu_usuario'))
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
    #roles 
    @app.route('/menu_admin')
    @rol_requerido(1)
    def menu_admin():
        if session.get('rol') == 1:
            return render_template('admin/menu_admin.html')
        flash("Acceso no autorizado", 'danger')
        return redirect(url_for('login_home'))

    @app.route('/menu_usuario')
    @rol_requerido(2)
    def menu_usuario():
        if session.get('rol') == 2:
            resultados = Producto.consulta_prod() 
            return render_template("usuario/consultar_prod_usu.html", datos=resultados)
        flash("Acceso no autorizado", 'danger')
        return redirect(url_for('login_home'))

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
        if not usuario_id:
            flash("Debes iniciar sesión para ver tus productos.", "warning")
            return redirect(url_for('login_home'))
        
        try:
            resultados = Producto.consulta_prod_por_usuario(usuario_id)
            return render_template("admin/consultar_prod_admin.html", datos=resultados)
        except Exception as e:
            flash(f"Error al consultar productos: {str(e)}", "danger")
            return redirect(url_for('login_home'))

    #----------------------------------------
    # Detalle de la consulta de productos
    #----------------------------------------
    @app.route('/producto/<int:id>')
    @rol_requerido(1)
    def ver_producto(id):
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            flash("Debes iniciar sesión para ver tus productos.", "warning")
            return redirect(url_for('login_home'))
        try:
            producto = Producto.obtener_producto_por_id(id)
            if producto:
                return render_template('admin/editar_prod_admin.html', producto=producto)
            else:
                flash("Producto no encontrado", "warning")
                return redirect(url_for('consulta_stock'))
        except Exception as e:
            flash(f"Error al obtener el producto: {str(e)}", "danger")
            return redirect(url_for('login_home'))
        

    #----------------------------------------
    # Detalle de la consulta de productos
    #----------------------------------------
    @app.route('/comprar/<int:id>')
    #@rol_requerido(2)
    def comprar_producto(id):
        # usuario_id = session.get('usuario_id')
        # if not usuario_id:
        #     flash("Debes iniciar sesión para ver tus productos.", "warning")
        #     return redirect(url_for('login_home'))
        try:
            producto = Producto.obtener_producto_por_id(id)
            if producto:
                return render_template('usuario/comprar_prod_usu.html', producto=producto)
            else:
                flash("Producto no encontrado", "warning")
                return redirect(url_for('consulta_stock'))
        except Exception as e:
            flash(f"Error al obtener el producto: {str(e)}", "danger")
            return redirect(url_for('login_home'))

    #----------------------------------------
    # Página para insertar producto
    #----------------------------------------
    @app.route('/insertar_producto', methods=['GET', 'POST'])
    @rol_requerido(1)
    def insertar_producto():
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            flash("Debes iniciar sesión para insertar productos.", "warning")
            return redirect(url_for('login_home'))

        if request.method == 'POST':
            try:
                nombre = request.form['nombre']
                precio = request.form['precio']
                disponible = 'disponible' in request.form
                marca = request.form['marca']
                descripcion = request.form['descripcion']

                exito = Producto.insertar_producto_en_db(nombre, precio, disponible, marca, descripcion, usuario_id)
                if exito:
                    flash("Producto insertado exitosamente.", "success")
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
        if not usuario_id:
            flash("Debes iniciar sesión para insertar detalles del producto.", "warning")
            return redirect(url_for('login_home'))

        try:
            if request.method == 'POST':
                talla = request.form['talla']
                color = request.form['color']
                stock = request.form['stock']

                exito = Producto.insertar_detalle_producto(producto_id, talla, color, stock)
                if exito:
                    flash("Detalle del producto insertado correctamente.", "success")
                    return redirect(url_for('insertar_detalles_producto', producto_id=producto_id))
                else:
                    flash("Error al insertar detalles del producto.", "danger")

            producto = Producto.obtener_producto_por_id(producto_id)
            if not producto:
                flash("Producto no encontrado", "warning")
                return redirect(url_for('consulta_stock'))

            producto_detalles = Producto.obtener_detalles_por_id(producto_id)
            return render_template('admin/insertar_prod_det_admin.html', 
                                producto_id=producto_id, 
                                producto_nombre=producto['nombre'], 
                                producto_detalles=producto_detalles)
        except Exception as e:
            flash(f"Ocurrió un error: {str(e)}", "danger")
            return redirect(url_for('consulta_stock'))

     #----------------------------------------
    # Página de la consulta de productos
    #----------------------------------------
    
    

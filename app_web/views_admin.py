from flask import render_template, request, redirect, url_for, session
from .models.admin.usuario_admin import Usuario
from .models.admin.producto_admin import Producto, AltaProductoException, AltaProductoPrecioException

def registrar_rutas(app):
    #----------------------------------------
    # Página de registro al sistema
    #----------------------------------------
    @app.route('/', methods=['GET', 'POST'])
    @app.route('/login', methods=['GET', 'POST'])
    def login_home():
        if request.method == 'POST':
            username = request.form['usuario']
            password = request.form['contrasena']

            usuario = Usuario.verificar_usuario(username, password)
            if usuario:
                session['usuario'] = usuario['nombre']
                session['correo'] = usuario['correo']
                session['rol'] = usuario['rol']

                if usuario['rol'] == 1:
                    return redirect(url_for('menu_admin'))
                elif usuario['rol'] == 2:
                    return redirect(url_for('menu_usuario'))
                else:
                    return "Rol no válido", 403
            else:
                return render_template('login.html', error="Credenciales incorrectas"), 401
        return render_template('login.html')


    #roles 
    @app.route('/menu_admin')
    def menu_admin():
        if session.get('rol') == 1:
            return render_template('admin/menu_admin.html')
        return redirect(url_for('login_home'))

    @app.route('/menu_usuario')
    def menu_usuario():
        if session.get('rol') == 2:
            return render_template('usuario/menu_usuario.html')
        return redirect(url_for('login_home'))

    #----------------------------------------    
    # Página  del menu principal
    #----------------------------------------
    @app.route('/inicio', methods=['GET', 'POST']) 
    def inicio_home():
            return render_template('admin/menu_admin.html')
    
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

            exito = Usuario.insertar_usuario_en_db(nombre, fecha_nacimiento, rol, correo, contrasena)
            if exito:
                return redirect(url_for('login_home'))
            else:
                return render_template('insertar_usuario.html', error="No se pudo registrar el usuario.")
        return render_template('insertar_usuario.html')


    @app.route('/perfil_usuario')
    def perfil_usuario():
        if 'usuario' in session:
            return render_template('perfil.html', usuario=session['usuario'], correo=session['correo'])
        return redirect(url_for('inicio_sesion'))
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login_home'))
    
    #----------------------------------------
    # Página de la consulta de productos
    #----------------------------------------
    @app.route('/consulta_productos', methods=['GET', 'POST'])
    def consulta_productos():
            resultados = Producto.consulta_prod()
            return render_template("admin/consultar_prod_admin.html", datos=resultados)
    
    #----------------------------------------
    # Detalle de la consulta de productos
    #----------------------------------------
    @app.route('/producto/<int:id>')
    def ver_producto(id):
        # Suponiendo que tienes una forma de buscar el producto por ID
        producto = Producto.obtener_producto_por_id(id)  # función que debes definir
        if producto:
            return render_template('producto.html', producto=producto)
        else:
            return "Producto no encontrado", 404

    #----------------------------------------
    # Página para insertar producto
    #----------------------------------------
    @app.route('/insertar_producto', methods=['GET', 'POST'])
    def insertar_producto():
        if request.method == 'POST':
            nombre = request.form['nombre']
            precio = request.form['precio']
            disponible = 'disponible' in request.form
            marca = request.form['marca']
            descripcion = request.form['descripcion']
            exito = Producto.insertar_producto_en_db(nombre, precio, disponible, marca, descripcion)
            if exito:
                return redirect(url_for('consulta_productos'))
            else:
                return "Error al insertar producto", 500
        return render_template('admin/insertar_prod_admin.html')
    
    @app.route('/insertar_detalles_producto/<int:producto_id>', methods=['GET', 'POST'])
    def insertar_detalles_producto(producto_id):
        if request.method == 'POST':
            talla = request.form['talla']
            color = request.form['color']
            stock = request.form['stock']

            exito = Producto.insertar_detalle_producto(producto_id, talla, color, stock)
            if exito:
                return redirect(url_for('consulta_productos'))
            else:
                return "Error al insertar detalles del producto", 500

        return render_template('admin/insertar_prod_det_admin.html', producto_id=producto_id)

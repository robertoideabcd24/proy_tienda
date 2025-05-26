from flask import render_template, request, redirect, url_for, flash, session
from functools import wraps
from models.admin.producto_admin import Producto
from models.usuario.carrito_usuario import Carrito


# Decorador si no lo importas globalmente
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

def registrar_rutas_usuario(app):

    
    @app.route('/producto_usuario/<int:id>')
    @rol_requerido(2)
    def ver_producto_usuario(id):
        try:
            producto = Producto.obtener_producto_por_id(id)
            if producto:
                return render_template('usuario/ver_producto_usuario.html', producto=producto)
            else:
                flash("Producto no encontrado", "warning")
                return redirect(url_for('menu_usuario'))
        except Exception as e:
            flash(f"Error al obtener el producto: {str(e)}", "danger")
            return redirect(url_for('menu_usuario'))


    @app.route('/agregar_carrito/<int:id>', methods=['POST'])
    def agregar_carrito(id):
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            flash("Debes iniciar sesión para agregar productos al carrito.", "warning")
            return redirect(url_for('login_home'))

        carrito_item = Carrito.obtener_por_usuario_y_producto(usuario_id, id)
        if carrito_item:
            carrito_item.cantidad += 1
            carrito_item.guardar()
        else:
            nuevo_item = Carrito(usuario_id=usuario_id, producto_id=id, cantidad=1)
            nuevo_item.guardar()

        flash("Producto agregado al carrito", "success")
        return redirect(url_for('menu_usuario'))



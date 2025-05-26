from flask import render_template, request, redirect, url_for, session, flash
from functools import wraps
from models.admin.usuario_admin import Usuario, UsuarioException
from models.admin.producto_admin import Producto, AltaProductoException, AltaProductoPrecioException, AltaProductoDescripcionException


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

#------------------------------------------------
# Página de la consulta de productos para usuario
#------------------------------------------------


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
        
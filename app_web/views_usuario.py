from flask import render_template, request, redirect, url_for, flash, session
from functools import wraps
from .models.admin.producto_admin import Producto
from .models.usuario.carrito_usuario import Carrito
from .extension import pgdb  # tu instancia de PostgresDB
from .models.usuario.compras import Compra


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

    @app.route('/agregar_carrito/<int:producto_id>', methods=['POST'])
    @rol_requerido(2)
    def agregar_carrito(producto_id):
        try:
            # Validar selección de detalle
            if 'detalle_seleccionado' not in request.form:
                flash("Debes seleccionar una talla y color", "danger")
                return redirect(url_for('comprar_producto', id=producto_id))

            detalle_index = int(request.form['detalle_seleccionado'])
            detalles = Producto.obtener_detalles_por_id(producto_id)
            
            if not detalles or detalle_index >= len(detalles):
                flash("Selección inválida", "danger")
                return redirect(url_for('comprar_producto', id=producto_id))
                
            detalle = detalles[detalle_index]
            talla, color, stock_disponible = detalle

            campo_cantidad = f'cantidad_{detalle_index}'
            cantidad = int(request.form.get(campo_cantidad, 1))

            if cantidad <= 0:
                flash("La cantidad debe ser mayor a cero", "danger")
                return redirect(url_for('comprar_producto', id=producto_id))

            if cantidad > stock_disponible:
                flash(f"No hay suficiente stock. Disponible: {stock_disponible}", "danger")
                return redirect(url_for('comprar_producto', id=producto_id))

            # Obtener usuario_id desde la sesión
            usuario_id = session.get('usuario_id')
            if not usuario_id:
                flash("Usuario no autenticado", "danger")
                return redirect(url_for('login_home'))

            # Acción: Comprar o Agregar al carrito
            accion = request.form.get('accion')
            if accion == 'comprar':
                # Actualizar stock
                exito, mensaje = Producto.actualizar_stock(producto_id, talla, color, cantidad)
                if not exito:
                    flash(mensaje, "danger")
                    return redirect(url_for('comprar_producto', id=producto_id))

                # Obtener precio del producto
                producto = Producto.obtener_producto_por_id(producto_id)
                precio = producto['precio'] if producto and 'precio' in producto else 0

                # Guardar la compra en el historial
                exito_compra, mensaje_compra = Compra.guardar_compra(
                    usuario_id, producto_id, talla, color, cantidad, precio
                )
                
                if not exito_compra:
                    flash(f"Error al registrar compra: {mensaje_compra}", "warning")
                else:
                    flash("Compra realizada con éxito. Stock actualizado.", "success")
                return redirect(url_for('comprar_producto', id=producto_id))
            
            else:
                # Agregar el producto al carrito
                Carrito.agregar_producto(usuario_id, producto_id, talla, color, cantidad)
                flash("Producto agregado al carrito", "success")
                return redirect(url_for('comprar_producto', id=producto_id))

        except ValueError:
            flash("Cantidad inválida", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

        return redirect(url_for('comprar_producto', id=producto_id))

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
        

    @app.route('/ver_carrito')
    @rol_requerido(2)  # Añade el decorador para requerir rol de usuario
    def ver_carrito():
        try:
            # Verificar que el usuario está autenticado
            if 'usuario_id' not in session:
                flash("Debes iniciar sesión para ver tu carrito", "warning")
                return redirect(url_for('login_home'))
            
            usuario_id = session['usuario_id']
            print(f" usuario_id en sesión: {usuario_id}")
            # Obtener los productos del carrito
            carrito = Carrito.obtener_todos_por_usuario(usuario_id)
            
            # Calcular el total
            total = sum(item['subtotal'] for item in carrito)
            
            # Renderizar la plantilla con los datos
            return render_template('usuario/ver_carrito.html', 
                                carrito=carrito, 
                                total=total)
        
        except Exception as e:
            flash(f"Error al cargar el carrito: {str(e)}", "danger")
            return redirect(url_for('consulta_productos'))
        

    @app.route('/pagar_carrito', methods=['POST'])
    @rol_requerido(2)
    def pagar_carrito():
        try:
            usuario_id = session.get('usuario_id')
            if not usuario_id:
                flash("Debes iniciar sesión para pagar", "warning")
                return redirect(url_for('login_home'))
            
            # Procesar pago y actualizar stock
            exito, mensaje = Carrito.procesar_pago(usuario_id)
            
            if exito:
                flash("¡Pago realizado con éxito! Stock actualizado", "success")
                return redirect(url_for('ver_carrito'))
            else:
                flash(f"Error al procesar pago: {mensaje}", "danger")
                return redirect(url_for('ver_carrito'))
                
        except Exception as e:
            flash(f"Error inesperado: {str(e)}", "danger")
            return redirect(url_for('ver_carrito'))
        
    @app.route('/eliminar_del_carrito', methods=['POST'])
    @rol_requerido(2)
    def eliminar_del_carrito():
        try:
            usuario_id = session.get('usuario_id')
            if not usuario_id:
                flash("Debes iniciar sesión para modificar el carrito", "warning")
                return redirect(url_for('login_home'))

            producto_id = int(request.form['producto_id'])
            talla = request.form['talla']
            color = request.form['color']

            Carrito.eliminar_producto(usuario_id, producto_id, talla, color)
            flash("Producto eliminado del carrito", "success")
        except Exception as e:
            flash(f"Error al eliminar producto del carrito: {str(e)}", "danger")
       
        return redirect(url_for('ver_carrito'))
    

    @app.route('/ver_compras')
    @rol_requerido(2)
    def ver_compras():
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            flash("Debes iniciar sesión para ver tus compras", "warning")
            return redirect(url_for('login_home'))

        compras = Compra.obtener_compras_usuario(usuario_id)  # <- Este método debes tenerlo definido
        return render_template('usuario/ver_compras.html', compras=compras)


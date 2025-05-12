from flask import Flask, request, redirect, url_for, render_template
from .extension import pgdb
from .views_admin import registrar_rutas


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'pipzas'
    registrar_rutas(app)

    return app

app = create_app()
pgdb.init_app(app)


if __name__ == "__main__":
    app.run(debug=True)
    #app.run()

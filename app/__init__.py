from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    CORS(app)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'zapatex.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'clave_secreta_segura'  # Necesario para sesiones / formularios

    db.init_app(app)

    # Importar y registrar blueprints
    from .routes.routes import api
    from app.routes.payments import bp as payments_bp

    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(payments_bp)  # Sin prefijo: accederás con /pagar

    with app.app_context():
        db.create_all()

    return app

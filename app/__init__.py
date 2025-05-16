# app/__init__.py

from flask import Flask # Deixe o resto do seu arquivo __init__.py como estava
from dotenv import load_dotenv
import os
# ... (o resto da sua função create_app, etc.) ...

# (Mantenha o resto do seu arquivo __init__.py como está)
# load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from . import routes
    app.register_blueprint(routes.bp)

    # from . import db_utils # Não vamos chamar init_db aqui por enquanto
    # db_utils.init_db()

    if not app.debug and not app.testing:
        import logging
        # ... (seu código de logging) ...

    print("--- APP/__INIT__.PY: Função create_app() está prestes a retornar app ---")
    return app

# app/__init__.py
from flask import Flask
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler

# Carrega variáveis de ambiente do arquivo .env
# É importante que isso seja chamado antes de qualquer configuração que dependa delas.
load_dotenv()
print("APP/__INIT__.PY: Variáveis de ambiente do .env deveriam estar carregadas.")

def create_app():
    print("--- APP/__INIT__.PY: Entrando em create_app() ---")
    app = Flask(__name__)

    # Configurações da Aplicação
    # SECRET_KEY é crucial para sessões e mensagens flash
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma_chave_secreta_padrao_muito_forte_e_aleatoria')
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads') # Salva em app/static/uploads/

    # Garante que a pasta de uploads exista
    # app.static_folder já é o caminho absoluto para a pasta static dentro de app/
    # mas se app.static_folder não for o que esperamos, podemos construir o caminho absoluto:
    # upload_dir_abs = os.path.join(app.root_path, app.static_folder, 'uploads')
    # os.makedirs(upload_dir_abs, exist_ok=True)
    # app.config['UPLOAD_FOLDER'] = upload_dir_abs
    # Por agora, vamos usar o caminho relativo à pasta static que o Flask define.
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    print(f"APP/__INIT__.PY: Pasta de uploads configurada para: {app.config['UPLOAD_FOLDER']}")


    # Registra o Blueprint das rotas
    from . import routes # Importa o módulo routes.py da pasta app
    app.register_blueprint(routes.bp)
    print("APP/__INIT__.PY: Blueprint 'routes.bp' registrado.")

    # Inicializa o banco de dados (apenas se necessário, ou crie um comando CLI para isso)
    # Para desenvolvimento, pode ser útil, mas em produção, geralmente é um passo separado.
    # Como já temos o script manual, vamos deixar comentado aqui para evitar recriação a cada reinício.
    # with app.app_context(): # Garante que estamos no contexto da aplicação
    #     from . import db_utils
    #     # db_utils.init_db() # Comentado para não recriar o banco a cada reinício do Flask
    #     print("APP/__INIT__.PY: db_utils importado (init_db() comentado).")


    # Configuração de Logging (útil para produção e depuração)
    if not app.debug and not app.testing: # Não configura se estiver em modo debug ou teste
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/cuidarbot.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('CuidarBot aplicação iniciada (modo não-debug).')

    print("--- APP/__INIT__.PY: Função create_app() está prestes a retornar app ---")
    return app

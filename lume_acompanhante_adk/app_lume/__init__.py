# lume_acompanhante_adk/app_lume/__init__.py
from flask import Flask
import os

print("APP_LUME/__INIT__.PY: Carregando...")

def create_lume_app(): # Renomeado para clareza
    print("--- APP_LUME: Entrando em create_lume_app() ---")
    app = Flask(__name__, template_folder='templates')

    # Chave secreta para sessões Flask
    # É MUITO IMPORTANTE que esta chave seja diferente da do CuidarBot principal
    # se ambos usarem a mesma porta ou domínio para cookies de sessão (o que não é o caso aqui)
    # Mas é uma boa prática ter chaves diferentes.
    app.config['SECRET_KEY'] = os.getenv('LUME_SECRET_KEY', 'uma_chave_secreta_para_lume_muito_diferente')

    # A API Key do Google é carregada em agente_core_lume.py

    from . import routes  # Importa as rotas específicas para este app
    app.register_blueprint(routes.bp_lume) # Assume que o blueprint em routes.py se chama bp_lume
    print("APP_LUME: Blueprint 'routes.bp_lume' registrado.")

    print("--- APP_LUME: Função create_lume_app() está prestes a retornar app ---")
    return app

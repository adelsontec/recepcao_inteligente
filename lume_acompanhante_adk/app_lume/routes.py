# lume_acompanhante_adk/app_lume/routes.py
from flask import Blueprint, render_template, request, jsonify, current_app, session
import os
import sys

# Adiciona a pasta pai (lume_acompanhante_adk) ao path para encontrar agente_core_lume
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import agente_core_lume
    # A inicialização dos agentes é feita uma vez quando agente_core_lume é importado
    # ou na primeira chamada a interagir_com_lume_e_rotear
except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO em routes.py (Lume): Não foi possível importar agente_core_lume: {e}")
    # Fallback se a importação falhar
    def interagir_com_lume_e_rotear(mensagem_usuario, estado_conversa_atual, user_id="err"):
        return "Erro: Lógica do agente Lume não carregada.", {}
    agente_core_lume = type('obj', (object,), {'interagir_com_lume_e_rotear' : interagir_com_lume_e_rotear})

print("APP_LUME/ROUTES.PY (v10.2 - Argumento Corrigido): Carregando...")

bp_lume = Blueprint('lume_chat', __name__, template_folder='templates', url_prefix='/lume')

def get_lume_session_state():
    user_id_key = 'lume_user_id_v10_2' # Nova chave para garantir reset se necessário
    state_key = 'lume_conversa_estado_v10_2'

    if user_id_key not in session:
        session[user_id_key] = f"web_lume_v10_2_{os.urandom(4).hex()}"
        current_app.logger.info(f"LUME_ROUTES: Novo User ID gerado: {session[user_id_key]}")

    if state_key not in session:
        session[state_key] = {"etapa_conversa": "inicio", "nome_usuario": None, "sentimento_previo": None}
        current_app.logger.info(f"LUME_ROUTES: Estado inicial para {session.get(user_id_key, 'UNKNOWN_USER')}: {session[state_key]}")

    return session[user_id_key], session[state_key]

@bp_lume.route('/')
def chat_page_lume():
    current_app.logger.info("LUME_ROUTES: Acessando /lume/")
    # Reseta o estado da conversa para uma nova visita à página
    session['lume_conversa_estado_v10_2'] = {"etapa_conversa": "inicio", "nome_usuario": None, "sentimento_previo": None}
    user_id, _ = get_lume_session_state()
    current_app.logger.info(f"LUME_ROUTES: Estado da conversa Lume RESETADO para {user_id}.")

    initial_page_message = "Bem-vindo(a)! Sou a Lume. 😊 Para começarmos, diga 'Olá'!"
    return render_template('chat_lume.html', initial_bot_message=initial_page_message)

@bp_lume.route('/send', methods=['POST'])
def send_message_lume():
    user_message = request.json.get('message', '').strip()
    adk_user, estado_conversa_atual_dict = get_lume_session_state()

    current_app.logger.info(f"LUME_ROUTES: User '{adk_user}' enviou: '{user_message}'. Estado ANTES: {estado_conversa_atual_dict}")

    if not user_message: return jsonify({'reply': "Por favor, diga algo."})

    if not hasattr(agente_core_lume, 'interagir_com_lume_e_rotear'):
        current_app.logger.error("LUME_ROUTES: agente_core_lume.interagir_com_lume_e_rotear não está disponível!")
        return jsonify({'reply': "Desculpe, estou com um problema técnico."}), 500

    try:
        # --- CORREÇÃO AQUI ---
        # O nome do parâmetro na função interagir_com_lume_e_rotear é 'estado_conversa_atual'
        bot_response_text, novo_estado_conversa = agente_core_lume.interagir_com_lume_e_rotear(
            mensagem_usuario=user_message,
            estado_conversa_atual=dict(estado_conversa_atual_dict), # Nome do argumento corrigido
            user_id=adk_user
        )

        session['lume_conversa_estado_v10_2'] = novo_estado_conversa
        session.modified = True
        current_app.logger.info(f"LUME_ROUTES: Bot respondeu: '{bot_response_text[:100]}...'. Estado DEPOIS: {session['lume_conversa_estado_v10_2']}")

        return jsonify({'reply': bot_response_text})
    except Exception as e:
        current_app.logger.error(f"LUME_ROUTES: Erro ao chamar interagir_com_lume_e_rotear: {e}", exc_info=True)
        return jsonify({'reply': "Desculpe, ocorreu um erro."}), 500

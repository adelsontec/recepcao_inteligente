# ~/recepcao_inteligente/app/routes.py
from flask import (
    Blueprint, render_template, request, jsonify,
    current_app, session, redirect, url_for, flash, Response
)
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date
import traceback
import re
from functools import wraps

from . import db_utils
from . import ocr_utils
from . import chatbot_utils

bp = Blueprint('main', __name__)

# --- Lógica de Autenticação (como antes) ---
def check_auth(username, password):
    admin_user = current_app.config.get('ADMIN_USERNAME', 'admin_fallback')
    admin_pass = current_app.config.get('ADMIN_PASSWORD', 'pass_fallback')
    if username == admin_user and password == admin_pass: return True
    return False
def authenticate():
    return Response('Acesso negado.', 401, {'WWW-Authenticate': 'Basic realm="Login Obrigatório"'})
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password): return authenticate()
        return f(*args, **kwargs)
    return decorated

# --- Funções de Sessão de Chat (como antes) ---
def get_current_chat_session():
    if 'serializable_chat_history' not in session:
        current_app.logger.info("ROUTES_FINAL_V2: Iniciando nova sessão de chat.")
        chat_session = chatbot_utils.model.start_chat(history=[])
        session['serializable_chat_history'] = []
    else:
        chat_session = chatbot_utils.model.start_chat(history=session['serializable_chat_history'])
    return chat_session

def save_chat_history_to_session(chat_session_obj):
    current_serializable_history = []
    if hasattr(chat_session_obj, 'history'):
        for content_message in chat_session_obj.history:
            message_dict = {'role': content_message.role, 'parts': []}
            if hasattr(content_message, 'parts'):
                for part in content_message.parts:
                    if hasattr(part, 'text'):
                        message_dict['parts'].append({'text': part.text})
            current_serializable_history.append(message_dict)
    session['serializable_chat_history'] = current_serializable_history


@bp.route('/')
def chat_page():
    session.pop('serializable_chat_history', None); session.pop('ocr_data', None)
    session.pop('image_path', None); session.pop('categoria_atendimento', None)
    session.pop('manual_input_step', None); session.pop('manual_data', None)
    initial_bot_message = "Olá! Eu sou o CuidarBot. Como posso te ajudar a iniciar seu atendimento hoje? Por favor, escolha o tipo de atendimento desejado."
    return render_template('chat.html', initial_message=initial_bot_message)

@bp.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.json.get('message', '').strip()
    chat_session_obj = get_current_chat_session()
    bot_response_text = ""
    action_response = None

    manual_input_step = session.get('manual_input_step')
    manual_data = session.get('manual_data', {})

    try:
        current_app.logger.info(f"ROUTES_FINAL_V2: /send_message: '{user_message}', Cat: {session.get('categoria_atendimento')}, ManualStep: {manual_input_step}")

        if manual_input_step:
            if manual_input_step == 'ask_name':
                manual_data['nome'] = user_message
                session['manual_input_step'] = 'ask_cpf'
                bot_response_text = "Entendido. Agora, por favor, qual o seu CPF?"
            elif manual_input_step == 'ask_cpf':
                cpf_digitado = re.sub(r'\D', '', user_message) # Limpa para validação
                if len(cpf_digitado) == 11: # Validação simples de tamanho
                    manual_data['cpf'] = user_message # Guarda o CPF como digitado
                    session['manual_input_step'] = 'ask_dob'
                    bot_response_text = "Obrigado. E qual a sua data de nascimento (no formato DD/MM/AAAA)?"
                else:
                    bot_response_text = "CPF inválido. Por favor, digite um CPF com 11 números (pode incluir pontos e traço)."
            elif manual_input_step == 'ask_dob':
                if re.match(r'^\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}$', user_message):
                    manual_data['data_nascimento'] = user_message
                    manual_data['idade'] = ocr_utils.calcular_idade(user_message)
                    session['manual_input_step'] = 'confirm_manual_data'

                    session['ocr_data'] = { # Coloca os dados manuais em ocr_data para o fluxo de confirmação
                        'nome': manual_data.get('nome'), 'cpf': manual_data.get('cpf'),
                        'data_nascimento': manual_data.get('data_nascimento'), 'idade': manual_data.get('idade'),
                        'texto_completo': "Dados inseridos manualmente."
                    }

                    prompt_confirm_manual = (
                        f"Por favor, confirme os dados que você forneceu:\n"
                        f"Nome: {manual_data.get('nome')}\n"
                        f"CPF: {manual_data.get('cpf')}\n"
                        f"Data de Nascimento: {manual_data.get('data_nascimento')}\n"
                        f"Idade Calculada: {manual_data.get('idade') if manual_data.get('idade') is not None else 'Não calculada'}\n\n"
                        f"Está tudo correto? (Responda 'sim' ou 'não')"
                    )
                    bot_response_text = chatbot_utils.get_bot_response(prompt_confirm_manual, chat_session_obj)
                    action_response = 'display_manual_confirmation'
                else:
                    bot_response_text = "Formato de data inválido. Por favor, use DD/MM/AAAA."

            elif manual_input_step == 'confirm_manual_data':
                if user_message.lower() == 'sim':
                    bot_response_text = "Obrigado por confirmar! A processar sua senha..."
                    action_response = 'proceed_to_confirm_data_route'
                    session.pop('manual_input_step', None); session.pop('manual_data', None)
                else:
                    session.pop('manual_input_step', None); session.pop('manual_data', None)
                    session.pop('ocr_data', None)
                    bot_response_text = "Entendido. Vamos tentar novamente desde o início. Por favor, envie uma foto do seu documento ou, se preferir, diga 'digitar dados' para inserir manualmente."
                    action_response = 'request_document_again'

            session['manual_data'] = manual_data

        elif not session.get('categoria_atendimento'):
            categorias_validas = ["EXAME", "CONSULTA", "DENTISTA", "CONSULTA MARCADA"]
            user_input_upper = user_message.upper()
            if user_input_upper in categorias_validas:
                session['categoria_atendimento'] = user_input_upper
                bot_response_text = f"Entendido! Para seu atendimento de {session['categoria_atendimento']}, por favor, envie uma foto de um documento..."
                action_response = 'request_document'
                # Não precisa enviar para o Gemini aqui, a resposta é direta
            else:
                bot_response_text = chatbot_utils.get_bot_response(user_message, chat_session_obj)
                if any(k in bot_response_text.lower() for k in ["escolha entre", "categoria", "tipo de atendimento"]):
                    action_response = 'ask_category'
        else: # Categoria definida, não está em input manual
            if "digitar dados" in user_message.lower() or user_message.lower() == "corrigir":
                session['manual_input_step'] = 'ask_name'
                session['manual_data'] = {}
                # Não precisa do Gemini para esta transição, a pergunta é fixa
                bot_response_text = "Entendido. Vamos inserir seus dados manualmente. Qual o seu nome completo?"
            else:
                bot_response_text = chatbot_utils.get_bot_response(user_message, chat_session_obj)
                if any(k in bot_response_text.lower() for k in ["documento", "foto", "identificação"]) and not session.get('ocr_data'):
                    action_response = 'request_document'

        # Salva o histórico APENAS se a resposta veio do Gemini
        if not manual_input_step or manual_input_step == 'confirm_manual_data': # Ou outras etapas que usam Gemini
            save_chat_history_to_session(chat_session_obj)

        json_response = {'reply': bot_response_text}
        if action_response: json_response['action'] = action_response
        return jsonify(json_response)
    except Exception as e:
        current_app.logger.error(f"ROUTES_FINAL_V2: Erro em send_message: {e}", exc_info=True)
        return jsonify({'reply': "Erro no servidor."}), 500

@bp.route('/upload_document', methods=['POST'])
def upload_document():
    current_app.logger.info(f"ROUTES_FINAL_V2: ROTA /upload_document ACESSADA")
    try:
        if 'document' not in request.files or not request.files['document'].filename:
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        file = request.files['document']; categoria_selecionada = session.get('categoria_atendimento')
        if not categoria_selecionada: return jsonify({'error': 'Categoria não selecionada.'}), 400

        filename = secure_filename(file.filename); upload_dir = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_dir, exist_ok=True); filepath = os.path.join(upload_dir, filename)
        file.save(filepath); session['image_path'] = filepath

        text = ocr_utils.extract_text_from_image(filepath)
        nome = ocr_utils.parse_nome(text) if text else None
        cpf = ocr_utils.parse_cpf(text) if text else None
        data_nascimento_str = ocr_utils.parse_data_nascimento(text) if text else None

        # Verifica se os campos essenciais foram encontrados
        if not (nome and cpf and data_nascimento_str and nome != "Nome não extraído"):
            current_app.logger.info("ROUTES_FINAL_V2: OCR falhou em dados essenciais. Iniciando input manual.")
            session['manual_input_step'] = 'ask_name'
            session['manual_data'] = {} # Limpa dados manuais anteriores
            chat_session_obj = get_current_chat_session()
            bot_ocr_fail_message = chatbot_utils.get_bot_response(
                "Não consegui ler todos os dados do seu documento (Nome, CPF, Data de Nascimento). Vamos tentar inserir manualmente. Qual o seu nome completo?",
                chat_session_obj
            )
            save_chat_history_to_session(chat_session_obj)
            return jsonify({'error': 'OCR falhou, iniciando manual', 'bot_reply': bot_ocr_fail_message, 'action': 'manual_input_start'}), 200

        idade = ocr_utils.calcular_idade(data_nascimento_str)
        ocr_data = {
            'nome': nome, 'cpf': cpf,
            'data_nascimento': data_nascimento_str, 'idade': idade,
            'texto_completo': text
        }
        session['ocr_data'] = ocr_data
        current_app.logger.info(f"ROUTES_FINAL_V2: Dados OCR parseados: {ocr_data}")

        confirmation_prompt = (
            f"Para {categoria_selecionada}, extraí:\n"
            f"Nome: {nome}\nCPF: {cpf}\n"
            f"Data de Nascimento: {data_nascimento_str}\nIdade: {idade if idade is not None else 'Não calculada'}\n\n"
            f"Confirma? Se não, diga 'corrigir'."
        )
        chat_session_obj = get_current_chat_session()
        bot_confirmation_request = chatbot_utils.get_bot_response(confirmation_prompt, chat_session_obj)
        save_chat_history_to_session(chat_session_obj)
        return jsonify({'message': 'Documento processado!', 'extracted_data': ocr_data, 'bot_reply': bot_confirmation_request})
    except Exception as e:
        current_app.logger.error(f"ROUTES_FINAL_V2: ERRO em /upload_document: {e}", exc_info=True)
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@bp.route('/confirm_data', methods=['POST'])
def confirm_data():
    # ... (Mesma lógica da v_final_com_flash_fix, mas usando os dados simplificados)
    current_app.logger.info(f"ROUTES_FINAL_V2: ROTA /confirm_data ACESSADA")
    try:
        ocr_data = session.get('ocr_data')
        image_path = session.get('image_path', None) # Pode ser None se input manual
        categoria_atendimento_atual = session.get('categoria_atendimento')

        if not ocr_data or not categoria_atendimento_atual:
            return jsonify({'error': 'Dados incompletos na sessão.'}), 400

        cpf_extraido = ocr_data.get('cpf')
        cpf_limpo_para_verificacao = re.sub(r'\D', '', cpf_extraido) if cpf_extraido else None
        hoje_str = date.today().isoformat()

        ticket_existente_info = None
        if cpf_limpo_para_verificacao:
            ticket_existente_info = db_utils.check_existing_ticket_overall(cpf_limpo_para_verificacao, hoje_str)

        if ticket_existente_info:
            senha_ja_emitida = ticket_existente_info['senha_formatada']; categoria_ja_emitida = ticket_existente_info['categoria_atendimento']
            chat_session_obj = get_current_chat_session()
            prompt_gemini_senha_existente = f"Usuário já tem senha ({senha_ja_emitida}) para {categoria_ja_emitida} hoje. Informe e sugira aguardar."
            bot_msg = chatbot_utils.get_bot_response(prompt_gemini_senha_existente, chat_session_obj)
            save_chat_history_to_session(chat_session_obj)
            session.pop('ocr_data', None); session.pop('image_path', None); session.pop('categoria_atendimento', None)
            return jsonify({'message': 'Senha já emitida.', 'senha': senha_ja_emitida, 'bot_reply': bot_msg, 'action': 'ticket_already_exists_today'})

        senha_formatada = db_utils.get_next_senha_for_category(categoria_atendimento_atual)
        if senha_formatada is None:
            return jsonify({'error': 'Não foi possível gerar a senha.'}), 500

        horario = datetime.now()
        db_utils.add_visitor(
            ocr_data.get('nome'), cpf_limpo_para_verificacao,
            image_path, categoria_atendimento_atual, senha_formatada,
            ocr_data.get('data_nascimento'), ocr_data.get('idade'), horario
        )

        final_message_prompt = f"Dados para {categoria_atendimento_atual} confirmados. Senha: {senha_formatada}. Informe, dê mensagem de encorajamento e diga que a tela reiniciará em 10 segundos."
        chat_session_obj = get_current_chat_session()
        bot_final_message = chatbot_utils.get_bot_response(final_message_prompt, chat_session_obj)
        save_chat_history_to_session(chat_session_obj)

        session.pop('ocr_data', None); session.pop('image_path', None); session.pop('categoria_atendimento', None)
        return jsonify({'message': 'Acesso registrado!', 'senha': senha_formatada, 'bot_reply': bot_final_message, 'action': 'reset_timer_10s'})
    except Exception as e:
        current_app.logger.error(f"ROUTES_FINAL_V2: ERRO em /confirm_data: {e}", exc_info=True)
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# --- Rotas /admin_filas e /admin_delete_visitor (como na versão cuidarbot_routes_final_flash_fix_v2) ---
# Cole o código dessas duas rotas aqui, ajustando os prints de log para ROUTES_FINAL_V2 se desejar.
@bp.route('/admin_filas')
@auth_required
def admin_filas():
    current_app.logger.info("ROUTES_FINAL_V2: Acessando página de admin.")
    try:
        visitantes_de_hoje = db_utils.get_todays_visitors()
        filas_por_categoria = {}
        contagem_por_categoria = {}
        total_atendimentos_hoje = len(visitantes_de_hoje) if visitantes_de_hoje else 0
        if visitantes_de_hoje:
            for visitante in visitantes_de_hoje:
                categoria = visitante['categoria_atendimento']
                if categoria not in filas_por_categoria:
                    filas_por_categoria[categoria] = []; contagem_por_categoria[categoria] = 0
                filas_por_categoria[categoria].append(visitante)
                contagem_por_categoria[categoria] += 1
        categorias_definidas = ["EXAME", "CONSULTA", "DENTISTA", "CONSULTA MARCADA"]
        for cat in categorias_definidas:
            if cat not in contagem_por_categoria: contagem_por_categoria[cat] = 0
            if cat not in filas_por_categoria: filas_por_categoria[cat] = []
        return render_template('admin_filas.html',
                               filas_por_categoria=filas_por_categoria,
                               hoje=date.today().strftime("%d/%m/%Y"),
                               total_atendimentos_hoje=total_atendimentos_hoje,
                               contagem_por_categoria=contagem_por_categoria)
    except Exception as e:
        current_app.logger.error(f"ROUTES_FINAL_V2: Erro em /admin_filas: {e}", exc_info=True)
        return "Erro ao carregar página de administração.", 500

@bp.route('/admin_delete_visitor/<int:visitor_id>', methods=['POST'])
@auth_required
def admin_delete_visitor(visitor_id):
    current_app.logger.info(f"ROUTES_FINAL_V2: Tentando apagar visitante ID: {visitor_id}")
    success = db_utils.delete_visitor_by_id(visitor_id)
    if success: flash(f"Registo ID {visitor_id} apagado!", "success")
    else: flash(f"Erro ao apagar registo ID {visitor_id}.", "error")
    return redirect(url_for('main.admin_filas'))

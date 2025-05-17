# app/routes.py
from flask import (
    Blueprint, render_template, request, jsonify,
    current_app, session, redirect, url_for, flash, Response # 'flash' JÁ ESTAVA AQUI, VERIFIQUE SE NÃO FOI REMOVIDO
)
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date
import traceback
import re
from functools import wraps

# Importe seus outros módulos
from . import db_utils
from . import ocr_utils
from . import chatbot_utils

bp = Blueprint('main', __name__)

# --- LÓGICA DE AUTENTICAÇÃO BÁSICA ---
def check_auth(username, password):
    """Verifica se o nome de usuário e senha estão corretos."""
    admin_user = current_app.config.get('ADMIN_USERNAME', 'admin_fallback')
    admin_pass = current_app.config.get('ADMIN_PASSWORD', 'pass_fallback')
    # Adiciona logs para depurar a autenticação
    current_app.logger.info(f"AUTH_CHECK: Tentando login com user: '{username}'. Esperado: '{admin_user}'")
    if username == admin_user and password == admin_pass:
        current_app.logger.info("AUTH_CHECK: Sucesso na verificação de credenciais.")
        return True
    current_app.logger.warning("AUTH_CHECK: Falha na verificação de credenciais.")
    return False

def authenticate():
    """Envia uma resposta 401 para pedir autenticação."""
    return Response(
    'Acesso negado. Você precisa se autenticar para acessar esta página.', 401,
    {'WWW-Authenticate': 'Basic realm="Login Obrigatório"'}) # Realm traduzido

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:
            current_app.logger.warning("AUTH_REQUIRED: Nenhuma credencial de autenticação fornecida.")
            return authenticate()

        # Log das credenciais recebidas (CUIDADO: não logar senhas em produção real)
        # current_app.logger.debug(f"AUTH_REQUIRED: Recebido auth.username: {auth.username}")
        # current_app.logger.debug(f"AUTH_REQUIRED: Recebido auth.password: [SENHA OCULTA NO LOG]")


        if not check_auth(auth.username, auth.password):
            current_app.logger.warning(f"AUTH_REQUIRED: Falha na autenticação para o usuário '{auth.username}'.")
            return authenticate()

        current_app.logger.info(f"AUTH_REQUIRED: Autenticação bem-sucedida para o usuário '{auth.username}'.")
        return f(*args, **kwargs)
    return decorated
# --- FIM DA LÓGICA DE AUTENTICAÇÃO ---


def get_current_chat_session():
    if 'serializable_chat_history' not in session or not session['serializable_chat_history']:
        current_app.logger.info("ROUTES_FINAL_FLASH_FIX: Iniciando nova sessão de chat do Gemini.")
        chat_session = chatbot_utils.model.start_chat(history=[])
        session['serializable_chat_history'] = []
    else:
        current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Recriando sessão de chat do Gemini com histórico.")
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
    session.pop('serializable_chat_history', None)
    session.pop('ocr_data', None)
    session.pop('image_path', None)
    session.pop('categoria_atendimento', None)
    initial_bot_message = "Olá! Eu sou o CuidarBot. Como posso te ajudar a iniciar seu atendimento hoje? Por favor, escolha o tipo de atendimento desejado."
    return render_template('chat.html', initial_message=initial_bot_message)

@bp.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.json.get('message', '').strip()
    chat_session_obj = get_current_chat_session()
    bot_response_text = ""
    action_response = None
    try:
        current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: /send_message: '{user_message}', Categoria na sessão: {session.get('categoria_atendimento')}")
        if not session.get('categoria_atendimento'):
            categorias_validas = ["EXAME", "CONSULTA", "DENTISTA", "CONSULTA MARCADA"]
            user_input_upper = user_message.upper()
            if user_input_upper in categorias_validas:
                session['categoria_atendimento'] = user_input_upper
                bot_response_text = f"Entendido! Para seu atendimento de {session['categoria_atendimento']}, por favor, envie uma foto de um documento de identificação com foto (RG, CPF ou Carteirinha do SUS)."
                action_response = 'request_document'
                current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Categoria '{user_input_upper}' definida. Bot vai pedir documento.")
                temp_history_for_gemini = list(session.get('serializable_chat_history', []))
                temp_history_for_gemini.append({'role': 'user', 'parts': [{'text': user_message}]})
                temp_history_for_gemini.append({'role': 'model', 'parts': [{'text': bot_response_text}]})
                chat_session_obj = chatbot_utils.model.start_chat(history=temp_history_for_gemini)
            else:
                current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Categoria não definida e input não é categoria. Enviando '{user_message}' para Gemini.")
                bot_response_text = chatbot_utils.get_bot_response(user_message, chat_session_obj)
                if "escolha entre" in bot_response_text.lower() or \
                   "categoria" in bot_response_text.lower() or \
                   "tipo de atendimento" in bot_response_text.lower():
                    action_response = 'ask_category'
        else:
            current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Categoria JÁ DEFINIDA como '{session.get('categoria_atendimento')}'. Enviando '{user_message}' para Gemini.")
            bot_response_text = chatbot_utils.get_bot_response(user_message, chat_session_obj)
            if "documento" in bot_response_text.lower() or "foto" in bot_response_text.lower() or \
               "identificação" in bot_response_text.lower():
                 if not session.get('ocr_data'):
                    action_response = 'request_document'

        save_chat_history_to_session(chat_session_obj)
        json_response = {'reply': bot_response_text}
        if action_response:
            json_response['action'] = action_response
        current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Respondendo de /send_message com: {json_response}")
        return jsonify(json_response)
    except Exception as e:
        current_app.logger.error(f"ROUTES_FINAL_FLASH_FIX: Erro em send_message: {e}", exc_info=True)
        detailed_error = traceback.format_exc()
        print(f"ROUTES_FINAL_FLASH_FIX: DETAILED ERROR in send_message: {detailed_error}")
        return jsonify({'reply': "Ocorreu um erro inesperado no servidor ao processar sua mensagem. Tente novamente."}), 500

@bp.route('/upload_document', methods=['POST'])
def upload_document():
    current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: ROTA /upload_document ACESSADA com método {request.method}")
    try:
        if 'document' not in request.files:
            current_app.logger.error("ROUTES_FINAL_FLASH_FIX: Nenhum arquivo 'document' na requisição.")
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        file = request.files['document']
        if file.filename == '':
            current_app.logger.error("ROUTES_FINAL_FLASH_FIX: Nome do arquivo vazio.")
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

        categoria_selecionada = session.get('categoria_atendimento')
        if not categoria_selecionada:
            current_app.logger.error("ROUTES_FINAL_FLASH_FIX: Categoria de atendimento não encontrada na sessão para upload.")
            return jsonify({'error': 'Categoria de atendimento não selecionada. Por favor, comece a conversa novamente.'}), 400

        if file:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)

            current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Salvando arquivo em: {filepath}")
            file.save(filepath)
            session['image_path'] = filepath
            current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Arquivo salvo. Chamando OCR para: {filepath}")

            text = ocr_utils.extract_text_from_image(filepath)

            if not text or not text.strip():
                current_app.logger.error("ROUTES_FINAL_FLASH_FIX: OCR não retornou texto utilizável.")
                chat_session_obj = get_current_chat_session()
                bot_ocr_fail_message = chatbot_utils.get_bot_response(
                    "O sistema não conseguiu ler os dados do seu documento. Por favor, tente enviar uma foto mais nítida, com boa iluminação e sem cortes.",
                    chat_session_obj
                )
                save_chat_history_to_session(chat_session_obj)
                return jsonify({'error': 'OCR falhou', 'bot_reply': bot_ocr_fail_message, 'action': 'request_document_again'}), 200

            current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Texto extraído do OCR: {text[:100]}...")

            nome = ocr_utils.parse_nome(text)
            cpf = ocr_utils.parse_cpf(text)
            rg = ocr_utils.parse_rg(text)
            cns = ocr_utils.parse_cns(text) if hasattr(ocr_utils, 'parse_cns') else None
            data_nascimento_str = ocr_utils.parse_data_nascimento(text)
            idade = ocr_utils.calcular_idade(data_nascimento_str) if data_nascimento_str else None

            ocr_data = {
                'nome': nome, 'cpf': cpf, 'rg': rg, 'cns': cns,
                'data_nascimento': data_nascimento_str,
                'idade': idade,
                'texto_completo': text
            }
            session['ocr_data'] = ocr_data
            current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Dados do OCR parseados: {ocr_data}")

            confirmation_prompt = (
                f"Para o atendimento de {categoria_selecionada}, extraí os seguintes dados do documento:\n"
                f"Nome: {nome if nome else 'Não encontrado'}\n"
                f"CPF: {cpf if cpf else 'Não encontrado'}\n"
                f"RG: {rg if rg else 'Não encontrado'}\n"
                f"CNS: {cns if cns else 'Não encontrado'}\n"
                f"Data de Nascimento: {data_nascimento_str if data_nascimento_str else 'Não encontrada'}\n"
                f"Idade Calculada: {idade if idade is not None else 'Não calculada'}\n\n"
                f"Por favor, peça ao usuário para confirmar se estão corretos. Se algo estiver faltando ou incorreto, peça para ele tentar enviar uma nova foto ou, se preferir, digitar os dados."
            )

            chat_session_obj = get_current_chat_session()
            bot_confirmation_request = chatbot_utils.get_bot_response(confirmation_prompt, chat_session_obj)
            save_chat_history_to_session(chat_session_obj)
            current_app.logger.info("ROUTES_FINAL_FLASH_FIX: Prompt de confirmação enviado ao Gemini e resposta recebida.")

            return jsonify({
                'message': 'Documento processado!',
                'extracted_data': ocr_data,
                'bot_reply': bot_confirmation_request
            })
        current_app.logger.error("ROUTES_FINAL_FLASH_FIX: Condição 'if file:' falhou inesperadamente em /upload_document.")
        return jsonify({'error': 'Erro inesperado no processamento do arquivo.'}), 500

    except Exception as e:
        current_app.logger.error(f"ROUTES_FINAL_FLASH_FIX: ERRO INESPERADO em /upload_document: {e}", exc_info=True)
        detailed_error = traceback.format_exc()
        print(f"ROUTES_FINAL_FLASH_FIX: DETAILED ERROR in /upload_document: {detailed_error}")
        return jsonify({'error': f'Ocorreu um erro interno no servidor ao processar o documento. Detalhes: {str(e)}'}), 500

@bp.route('/confirm_data', methods=['POST'])
def confirm_data():
    current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: ROTA /confirm_data ACESSADA")
    try:
        ocr_data = session.get('ocr_data')
        image_path = session.get('image_path')
        categoria_atendimento_atual = session.get('categoria_atendimento')

        if not ocr_data or not image_path or not categoria_atendimento_atual:
            current_app.logger.error("ROUTES_FINAL_FLASH_FIX: Dados incompletos na sessão para /confirm_data.")
            return jsonify({'error': 'Dados incompletos na sessão. Por favor, comece novamente.'}), 400

        cpf_extraido = ocr_data.get('cpf')
        cpf_limpo_para_verificacao = re.sub(r'\D', '', cpf_extraido) if cpf_extraido else None

        hoje_str = date.today().isoformat()

        ticket_existente_info = None
        if cpf_limpo_para_verificacao:
            ticket_existente_info = db_utils.check_existing_ticket_overall(cpf_limpo_para_verificacao, hoje_str)

        if ticket_existente_info:
            senha_ja_emitida = ticket_existente_info['senha_formatada']
            categoria_ja_emitida = ticket_existente_info['categoria_atendimento']
            current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Usuário com CPF já possui senha {senha_ja_emitida} para {categoria_ja_emitida} hoje.")

            chat_session_obj = get_current_chat_session()
            prompt_gemini_senha_existente = f"Verifiquei aqui e o usuário já possui uma senha ({senha_ja_emitida}) para o atendimento de {categoria_ja_emitida} emitida hoje. Só é permitida uma senha por dia, independentemente da categoria. Por favor, informe isso ao usuário e diga para ele aguardar ser chamado ou se dirigir ao balcão se precisar de ajuda."
            bot_already_has_ticket_message = chatbot_utils.get_bot_response(prompt_gemini_senha_existente, chat_session_obj)
            save_chat_history_to_session(chat_session_obj)
            session.pop('ocr_data', None)
            session.pop('image_path', None)
            session.pop('categoria_atendimento', None)
            return jsonify({'message': 'Senha já emitida.', 'senha': senha_ja_emitida, 'bot_reply': bot_already_has_ticket_message, 'action': 'ticket_already_exists_today'})

        senha_formatada = db_utils.get_next_senha_for_category(categoria_atendimento_atual)
        if senha_formatada is None:
            current_app.logger.error("ROUTES_FINAL_FLASH_FIX: Falha ao gerar nova senha em /confirm_data.")
            return jsonify({'error': 'Não foi possível gerar a senha. Tente novamente mais tarde.'}), 500

        horario = datetime.now()

        db_utils.add_visitor(
            ocr_data.get('nome'),
            cpf_limpo_para_verificacao,
            ocr_data.get('rg'),
            ocr_data.get('cns'),
            image_path,
            categoria_atendimento_atual,
            senha_formatada,
            ocr_data.get('data_nascimento'),
            ocr_data.get('idade'),
            horario
        )

        final_message_prompt = f"Os dados para {categoria_atendimento_atual} foram confirmados e sua nova senha de atendimento é {senha_formatada}. Por favor, informe esta senha ao usuário e dê uma mensagem final de encorajamento."

        chat_session_obj = get_current_chat_session()
        bot_final_message = chatbot_utils.get_bot_response(final_message_prompt, chat_session_obj)
        save_chat_history_to_session(chat_session_obj)

        session.pop('ocr_data', None)
        session.pop('image_path', None)
        session.pop('categoria_atendimento', None)
        current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Visitante registrado e senha {senha_formatada} gerada para categoria {categoria_atendimento_atual}.")

        return jsonify({'message': 'Dados confirmados e acesso registrado!', 'senha': senha_formatada, 'bot_reply': bot_final_message})
    except Exception as e:
        current_app.logger.error(f"ROUTES_FINAL_FLASH_FIX: ERRO INESPERADO em /confirm_data: {e}", exc_info=True)
        detailed_error = traceback.format_exc()
        print(f"ROUTES_FINAL_FLASH_FIX: DETAILED ERROR in /confirm_data: {detailed_error}")
        return jsonify({'error': f'Ocorreu um erro interno no servidor ao registrar o acesso. Detalhes: {str(e)}'}), 500

@bp.route('/admin_filas')
@auth_required
def admin_filas():
    current_app.logger.info("ROUTES_FINAL_FLASH_FIX: Acessando página de administração de filas.")
    try:
        visitantes_de_hoje = db_utils.get_todays_visitors()
        filas_por_categoria = {}
        contagem_por_categoria = {}
        total_atendimentos_hoje = 0
        if visitantes_de_hoje:
            total_atendimentos_hoje = len(visitantes_de_hoje)
            for visitante_row in visitantes_de_hoje:
                visitante = dict(visitante_row)
                categoria = visitante['categoria_atendimento']
                if categoria not in filas_por_categoria:
                    filas_por_categoria[categoria] = []
                    contagem_por_categoria[categoria] = 0
                filas_por_categoria[categoria].append(visitante)
                contagem_por_categoria[categoria] += 1
        categorias_definidas = ["EXAME", "CONSULTA", "DENTISTA", "CONSULTA MARCADA"]
        for cat in categorias_definidas:
            if cat not in contagem_por_categoria:
                contagem_por_categoria[cat] = 0
            if cat not in filas_por_categoria:
                 filas_por_categoria[cat] = []
        current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Total atendimentos hoje: {total_atendimentos_hoje}")
        current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Contagem por categoria: {contagem_por_categoria}")
        return render_template('admin_filas.html',
                               filas_por_categoria=filas_por_categoria,
                               hoje=date.today().strftime("%d/%m/%Y"),
                               total_atendimentos_hoje=total_atendimentos_hoje,
                               contagem_por_categoria=contagem_por_categoria)
    except Exception as e:
        current_app.logger.error(f"ROUTES_FINAL_FLASH_FIX: Erro ao carregar página de admin: {e}", exc_info=True)
        detailed_error = traceback.format_exc()
        print(f"ROUTES_FINAL_FLASH_FIX: DETAILED ERROR in /admin_filas: {detailed_error}")
        return "Erro ao carregar a página de administração. Verifique os logs do servidor.", 500

@bp.route('/admin_delete_visitor/<int:visitor_id>', methods=['POST'])
@auth_required
def admin_delete_visitor(visitor_id):
    current_app.logger.info(f"ROUTES_FINAL_FLASH_FIX: Tentando apagar visitante com ID: {visitor_id}")
    success = db_utils.delete_visitor_by_id(visitor_id)
    if success:
        flash(f"Registo do visitante ID {visitor_id} apagado com sucesso!", "success")
    else:
        flash(f"Erro ao tentar apagar registo do visitante ID {visitor_id}.", "error")
    return redirect(url_for('main.admin_filas'))


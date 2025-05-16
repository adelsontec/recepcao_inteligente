# app/routes.py
from flask import Blueprint, render_template, request, jsonify, current_app, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date # Certifique-se que 'date' está importado
import traceback
import re

# Importe seus outros módulos
from . import db_utils
from . import ocr_utils
from . import chatbot_utils

# Defina o Blueprint 'bp' ANTES de usá-lo nas rotas
bp = Blueprint('main', __name__)

# (get_current_chat_session e save_chat_history_to_session permanecem as mesmas)
def get_current_chat_session():
    if 'serializable_chat_history' not in session or not session['serializable_chat_history']:
        current_app.logger.info("ROUTES_ADMIN_V2: Iniciando nova sessão de chat do Gemini.")
        chat_session = chatbot_utils.model.start_chat(history=[])
        session['serializable_chat_history'] = []
    else:
        current_app.logger.info(f"ROUTES_ADMIN_V2: Recriando sessão de chat do Gemini com histórico.")
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
    # ... (código da função send_message como na versão routes_fix_category_and_404 ou routes_one_ticket_per_day_overall_check)
    # Apenas garanta que os prints de log usem um identificador consistente se quiser, ex: ROUTES_ADMIN_V2
    user_message = request.json.get('message', '').strip()
    chat_session_obj = get_current_chat_session()
    bot_response_text = ""
    action_response = None
    try:
        current_app.logger.info(f"ROUTES_ADMIN_V2: /send_message: '{user_message}', Categoria na sessão: {session.get('categoria_atendimento')}")
        if not session.get('categoria_atendimento'):
            categorias_validas = ["EXAME", "CONSULTA", "DENTISTA", "CONSULTA MARCADA"]
            user_input_upper = user_message.upper()
            if user_input_upper in categorias_validas:
                session['categoria_atendimento'] = user_input_upper
                bot_response_text = f"Entendido! Para seu atendimento de {session['categoria_atendimento']}, por favor, envie uma foto de um documento de identificação com foto (RG, CPF ou Carteirinha do SUS)."
                action_response = 'request_document'
                current_app.logger.info(f"ROUTES_ADMIN_V2: Categoria '{user_input_upper}' definida. Bot vai pedir documento.")
                temp_history_for_gemini = list(session.get('serializable_chat_history', []))
                temp_history_for_gemini.append({'role': 'user', 'parts': [{'text': user_message}]})
                temp_history_for_gemini.append({'role': 'model', 'parts': [{'text': bot_response_text}]})
                chat_session_obj = chatbot_utils.model.start_chat(history=temp_history_for_gemini)
            else:
                current_app.logger.info(f"ROUTES_ADMIN_V2: Categoria não definida e input não é categoria. Enviando '{user_message}' para Gemini.")
                bot_response_text = chatbot_utils.get_bot_response(user_message, chat_session_obj)
                if "escolha entre" in bot_response_text.lower() or \
                   "categoria" in bot_response_text.lower() or \
                   "tipo de atendimento" in bot_response_text.lower():
                    action_response = 'ask_category'
        else:
            current_app.logger.info(f"ROUTES_ADMIN_V2: Categoria JÁ DEFINIDA como '{session.get('categoria_atendimento')}'. Enviando '{user_message}' para Gemini.")
            bot_response_text = chatbot_utils.get_bot_response(user_message, chat_session_obj)
            if "documento" in bot_response_text.lower() or "foto" in bot_response_text.lower() or \
               "identificação" in bot_response_text.lower():
                action_response = 'request_document'
        save_chat_history_to_session(chat_session_obj)
        json_response = {'reply': bot_response_text}
        if action_response:
            json_response['action'] = action_response
        current_app.logger.info(f"ROUTES_ADMIN_V2: Respondendo de /send_message com: {json_response}")
        return jsonify(json_response)
    except Exception as e:
        current_app.logger.error(f"ROUTES_ADMIN_V2: Erro em send_message: {e}", exc_info=True)
        detailed_error = traceback.format_exc()
        print(f"ROUTES_ADMIN_V2: DETAILED ERROR in send_message: {detailed_error}")
        return jsonify({'reply': "Ocorreu um erro inesperado no servidor ao processar sua mensagem. Tente novamente."}), 500

@bp.route('/upload_document', methods=['POST'])
def upload_document():
    # ... (código da função upload_document como na versão routes_fix_category_and_404 ou routes_one_ticket_per_day_overall_check)
    # Apenas garanta que os prints de log usem um identificador consistente se quiser, ex: ROUTES_ADMIN_V2
    current_app.logger.info(f"ROUTES_ADMIN_V2: ROTA /upload_document ACESSADA com método {request.method}")
    try:
        if 'document' not in request.files:
            current_app.logger.error("ROUTES_ADMIN_V2: Nenhum arquivo 'document' na requisição.")
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        file = request.files['document']
        if file.filename == '':
            current_app.logger.error("ROUTES_ADMIN_V2: Nome do arquivo vazio.")
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

        categoria_selecionada = session.get('categoria_atendimento')
        if not categoria_selecionada:
            current_app.logger.error("ROUTES_ADMIN_V2: Categoria de atendimento não encontrada na sessão para upload.")
            return jsonify({'error': 'Categoria de atendimento não selecionada. Por favor, comece a conversa novamente.'}), 400

        if file:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)

            current_app.logger.info(f"ROUTES_ADMIN_V2: Salvando arquivo em: {filepath}")
            file.save(filepath)
            session['image_path'] = filepath
            current_app.logger.info(f"ROUTES_ADMIN_V2: Arquivo salvo. Chamando OCR para: {filepath}")

            text = ocr_utils.extract_text_from_image(filepath)

            if not text or not text.strip():
                current_app.logger.error("ROUTES_ADMIN_V2: OCR não retornou texto utilizável.")
                chat_session_obj = get_current_chat_session()
                bot_ocr_fail_message = chatbot_utils.get_bot_response(
                    "O sistema não conseguiu ler os dados do seu documento. Por favor, tente enviar uma foto mais nítida, com boa iluminação e sem cortes.",
                    chat_session_obj
                )
                save_chat_history_to_session(chat_session_obj)
                return jsonify({'error': 'OCR falhou', 'bot_reply': bot_ocr_fail_message, 'action': 'request_document_again'}), 200

            current_app.logger.info(f"ROUTES_ADMIN_V2: Texto extraído do OCR: {text[:100]}...")

            nome = ocr_utils.parse_nome(text)
            cpf = ocr_utils.parse_cpf(text)
            rg = ocr_utils.parse_rg(text)
            cns = ocr_utils.parse_cns(text) if hasattr(ocr_utils, 'parse_cns') else None

            ocr_data = {'nome': nome, 'cpf': cpf, 'rg': rg, 'cns': cns, 'texto_completo': text}
            session['ocr_data'] = ocr_data
            current_app.logger.info(f"ROUTES_ADMIN_V2: Dados do OCR parseados: {ocr_data}")

            confirmation_prompt = f"Para o atendimento de {categoria_selecionada}, extraí os seguintes dados do documento: Nome: {nome if nome else 'Não encontrado'}, CPF: {cpf if cpf else 'Não encontrado'}, RG: {rg if rg else 'Não encontrado'}, CNS: {cns if cns else 'Não encontrado'}. Por favor, peça ao usuário para confirmar se estão corretos. Se algo estiver faltando ou incorreto, peça para ele digitar."

            chat_session_obj = get_current_chat_session()
            bot_confirmation_request = chatbot_utils.get_bot_response(confirmation_prompt, chat_session_obj)
            save_chat_history_to_session(chat_session_obj)
            current_app.logger.info("ROUTES_ADMIN_V2: Prompt de confirmação enviado ao Gemini e resposta recebida.")

            return jsonify({
                'message': 'Documento processado!',
                'extracted_data': ocr_data,
                'bot_reply': bot_confirmation_request
            })
        current_app.logger.error("ROUTES_ADMIN_V2: Condição 'if file:' falhou inesperadamente em /upload_document.")
        return jsonify({'error': 'Erro inesperado no processamento do arquivo.'}), 500
    except Exception as e:
        current_app.logger.error(f"ROUTES_ADMIN_V2: ERRO INESPERADO em /upload_document: {e}", exc_info=True)
        detailed_error = traceback.format_exc()
        print(f"ROUTES_ADMIN_V2: DETAILED ERROR in /upload_document: {detailed_error}")
        return jsonify({'error': f'Ocorreu um erro interno no servidor ao processar o documento. Detalhes: {str(e)}'}), 500

@bp.route('/confirm_data', methods=['POST'])
def confirm_data():
    # ... (código da função confirm_data como na versão routes_one_ticket_per_day_overall_check)
    # Apenas garanta que os prints de log usem um identificador consistente se quiser, ex: ROUTES_ADMIN_V2
    current_app.logger.info(f"ROUTES_ADMIN_V2: ROTA /confirm_data ACESSADA")
    try:
        ocr_data = session.get('ocr_data')
        image_path = session.get('image_path')
        categoria_atendimento_atual = session.get('categoria_atendimento')
        cpf_extraido = ocr_data.get('cpf') if ocr_data else None
        if not ocr_data or not image_path or not categoria_atendimento_atual:
            current_app.logger.error("ROUTES_ADMIN_V2: Dados incompletos na sessão para /confirm_data.")
            return jsonify({'error': 'Dados incompletos na sessão. Por favor, comece novamente.'}), 400
        cpf_limpo_para_verificacao = None
        if cpf_extraido:
            cpf_limpo_para_verificacao = re.sub(r'\D', '', cpf_extraido)
        hoje_str = date.today().isoformat()
        ticket_existente_info = None
        if cpf_limpo_para_verificacao:
            ticket_existente_info = db_utils.check_existing_ticket_overall(cpf_limpo_para_verificacao, hoje_str)
        if ticket_existente_info:
            senha_ja_emitida = ticket_existente_info['senha_formatada']
            categoria_ja_emitida = ticket_existente_info['categoria_atendimento']
            current_app.logger.info(f"ROUTES_ADMIN_V2: Usuário com CPF já possui senha {senha_ja_emitida} para {categoria_ja_emitida} hoje.")
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
            current_app.logger.error("ROUTES_ADMIN_V2: Falha ao gerar nova senha em /confirm_data.")
            return jsonify({'error': 'Não foi possível gerar a senha. Tente novamente mais tarde.'}), 500
        horario = datetime.now()
        db_utils.add_visitor(
            ocr_data.get('nome'), cpf_limpo_para_verificacao, ocr_data.get('rg'),
            ocr_data.get('cns'), image_path, categoria_atendimento_atual,
            senha_formatada, horario
        )
        final_message_prompt = f"Os dados para {categoria_atendimento_atual} foram confirmados e sua nova senha de atendimento é {senha_formatada}. Por favor, informe esta senha ao usuário e dê uma mensagem final de encorajamento."
        chat_session_obj = get_current_chat_session()
        bot_final_message = chatbot_utils.get_bot_response(final_message_prompt, chat_session_obj)
        save_chat_history_to_session(chat_session_obj)
        session.pop('ocr_data', None)
        session.pop('image_path', None)
        session.pop('categoria_atendimento', None)
        current_app.logger.info(f"ROUTES_ADMIN_V2: Visitante registrado e senha {senha_formatada} gerada para categoria {categoria_atendimento_atual}.")
        return jsonify({'message': 'Dados confirmados e acesso registrado!', 'senha': senha_formatada, 'bot_reply': bot_final_message})
    except Exception as e:
        current_app.logger.error(f"ROUTES_ADMIN_V2: ERRO INESPERADO em /confirm_data: {e}", exc_info=True)
        detailed_error = traceback.format_exc()
        print(f"ROUTES_ADMIN_V2: DETAILED ERROR in /confirm_data: {detailed_error}")
        return jsonify({'error': f'Ocorreu um erro interno no servidor ao registrar o acesso. Detalhes: {str(e)}'}), 500

# --- NOVA ROTA PARA A PÁGINA DE ADMINISTRAÇÃO ---
@bp.route('/admin_filas')
def admin_filas():
    current_app.logger.info("ROUTES_ADMIN_V2: Acessando página de administração de filas.")
    try:
        visitantes_de_hoje = db_utils.get_todays_visitors()
        filas_por_categoria = {}
        if visitantes_de_hoje:
            for visitante_row in visitantes_de_hoje: # visitante_row é um sqlite3.Row
                # Converte sqlite3.Row para um dicionário padrão
                visitante = dict(visitante_row)
                categoria = visitante['categoria_atendimento']
                if categoria not in filas_por_categoria:
                    filas_por_categoria[categoria] = []
                filas_por_categoria[categoria].append(visitante)
        current_app.logger.info(f"ROUTES_ADMIN_V2: Filas por categoria para admin: {list(filas_por_categoria.keys())}")
        return render_template('admin_filas.html', filas_por_categoria=filas_por_categoria, hoje=date.today().strftime("%d/%m/%Y"))
    except Exception as e:
        current_app.logger.error(f"ROUTES_ADMIN_V2: Erro ao carregar página de admin: {e}", exc_info=True)
        detailed_error = traceback.format_exc()
        print(f"ROUTES_ADMIN_V2: DETAILED ERROR in /admin_filas: {detailed_error}")
        return "Erro ao carregar a página de administração. Verifique os logs do servidor.", 500


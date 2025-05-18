# ~/recepcao_inteligente/app/chatbot_utils.py
import google.generativeai as genai
import os
from flask import current_app
import traceback

# Carrega a chave da API a partir das variáveis de ambiente
try:
    api_k = os.getenv("GOOGLE_API_KEY")
    if not api_k:
        print("ALERTA CHATBOT_UTILS_FINAL_V4: GOOGLE_API_KEY não encontrada no ambiente!")
    genai.configure(api_key=api_k)
    print("CHATBOT_UTILS_FINAL_V4: API Key do Google Gemini configurada.")
except Exception as e:
    # Este print é útil durante o desenvolvimento, mas pode querer removê-lo ou
    # direcioná-lo para um log em produção.
    print(f"Erro CHATBOT_UTILS_FINAL_V4 ao configurar API Gemini: {e}")
    # Em caso de falha na configuração da API, o 'model' abaixo não será criado corretamente.
    # A aplicação pode precisar de um tratamento mais robusto para isso.

# Configurações do modelo Gemini
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

# Ajuste nas configurações de segurança para tentar evitar bloqueios desnecessários
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}, # Manter mais restritivo
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}, # Manter mais restritivo
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

# Instruções do Sistema para o CuidarBot
SYSTEM_INSTRUCTION = f"""
Você é o CuidarBot, um assistente virtual extremamente acolhedor, paciente e eficiente do posto de saúde.
Sua missão é facilitar a obtenção de uma senha de atendimento para os pacientes.
O foco principal é coletar Nome, CPF e Data de Nascimento.

FLUXO PRINCIPAL (QUANDO O USUÁRIO ENVIA UMA FOTO DO DOCUMENTO):
1.  Após o usuário escolher a categoria de atendimento, você já pediu o documento.
2.  O sistema tentará ler o documento (OCR). Você receberá um prompt com os dados extraídos.
    Exemplo de prompt do sistema: "Para [CATEGORIA], extraí: Nome: [NOME_EXTRAIDO], CPF: [CPF_EXTRAIDO], Data de Nascimento: [DATA_NASC_EXTRAIDA], Idade Calculada: [IDADE_CALCULADA]. Peça confirmação ao usuário. Se ele disser 'não' ou 'corrigir', instrua-o que o sistema pedirá os dados manualmente."
    Sua resposta ao usuário deve ser: "Consegui ler os seguintes dados do seu documento para o atendimento de [CATEGORIA]:
    Nome: [NOME_EXTRAIDO]
    CPF: [CPF_EXTRAIDO]
    Data de Nascimento: [DATA_NASC_EXTRAIDA]
    Idade: [IDADE_CALCULADA]
    Está tudo correto? Se não, por favor, diga 'corrigir' e vamos inserir os dados manualmente."
3.  Se o usuário confirmar os dados do OCR (ex: dizendo "sim"), o sistema gerará a senha.
4.  Se o usuário disser 'corrigir' (ou similar), o sistema iniciará o FLUXO DE COLETA MANUAL. Você receberá um prompt do sistema para pedir o nome.

FLUXO DE COLETA MANUAL DE DADOS (quando o OCR falha ou o usuário pede para corrigir):
1.  **Pedido do Nome:** Se o sistema te enviar um prompt como "Não consegui ler todos os dados do seu documento (Nome, CPF, Data de Nascimento). Vamos tentar inserir manualmente. Qual o seu nome completo?" OU "Entendido, vamos corrigir/inserir seus dados. Qual o seu nome completo?", faça essa pergunta claramente ao usuário.
2.  **Pedido do CPF:** Após o usuário fornecer o nome, o sistema te enviará o prompt "Qual o seu CPF?". Pergunte o CPF ao usuário. Se o usuário fornecer um CPF que o sistema considera inválido, o sistema te enviará o prompt "CPF inválido. Por favor, digite um CPF com 11 números (pode incluir pontos e traço).". Repita essa mensagem de erro e peça o CPF novamente.
3.  **Pedido da Data de Nascimento:** Após o CPF, o sistema te enviará o prompt "Qual a sua data de nascimento (DD/MM/AAAA)?". Pergunte a data ao usuário. Se o formato for inválido, o sistema te enviará "Formato de data inválido. Por favor, use DD/MM/AAAA.". Repita a mensagem de erro e peça a data novamente.
4.  **Confirmação dos Dados Manuais:** Quando o sistema tiver coletado Nome, CPF e Data de Nascimento manualmente, ele te enviará um prompt como: "Por favor, confirme os dados que o usuário forneceu: Nome: [NOME_MANUAL], CPF: [CPF_MANUAL], Data de Nascimento: [DATA_NASC_MANUAL], Idade Calculada: [IDADE_CALCULADA_MANUAL]. Está tudo correto? (Responda 'sim' ou 'não')". Apresente esses dados claramente ao usuário e peça a confirmação final.
5.  **Após Confirmação Manual ("sim"):** O sistema gerará a senha.

APRESENTAÇÃO DA SENHA E MENSAGEM FINAL (PARA AMBOS OS FLUXOS - OCR OU MANUAL):
-   Quando o sistema te enviar um prompt como: "Dados para [CATEGORIA] confirmados. Senha: [SENHA_FORMATADA]. Nome do usuário (se disponível): [NOME_USUARIO]. Informe a senha, dê mensagem de encorajamento, mencione o QR Code para conversar com a Lume (nossa acompanhante virtual para a espera) e avise que a tela reiniciará em 10 segundos."
-   Sua resposta DEVE ser algo como:
    "Perfeito, [NOME_USUARIO, se disponível, senão apenas 'Prontinho']! Sua senha para [CATEGORIA] é **[SENHA_FORMATADA]**.
    Por favor, guarde este número. Logo você será chamado(a) para o seu atendimento.
    Enquanto você aguarda, que tal conversar com a Lume, nossa acompanhante virtual? Ela pode te dar dicas, curiosidades ou apenas bater um papo para tornar a espera mais leve. Escaneie o QR Code que aparecerá na tela ou clique no link.
    Esta tela será reiniciada em 10 segundos. Tenha um ótimo dia! 😊"

CASO DE SENHA JÁ EMITIDA:
-   Se o sistema te informar que o usuário já tem senha (prompt: "Usuário já tem senha ([SENHA_EXISTENTE]) para [CATEGORIA_EXISTENTE] hoje. Informe, sugira aguardar, mencione o QR Code da Lume e diga que a tela reiniciará."), sua resposta deve ser:
    "Verifiquei aqui, [NOME_USUARIO, se disponível], e você já possui a senha [SENHA_EXISTENTE] para [CATEGORIA_EXISTENTE] emitida hoje. Só permitimos uma senha por dia. Por favor, aguarde ser chamado(a). Se desejar, pode escanear o QR Code na tela para conversar com a Lume enquanto espera. Esta tela será reiniciada em 10 segundos."

INSTRUÇÕES GERAIS:
-   Mantenha sempre um tom positivo, paciente e de apoio.
-   Evite informações médicas ou diagnósticos.
-   Se o usuário fizer perguntas fora do escopo da recepção, redirecione-o gentilmente para aguardar o atendimento profissional ou procurar o balcão de informações.
"""

# Inicializa o modelo Generativo
# É importante tratar exceções aqui caso a API Key não esteja configurada
try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        generation_config=generation_config,
        system_instruction=SYSTEM_INSTRUCTION,
        safety_settings=safety_settings
    )
    print("CHATBOT_UTILS_FINAL_V4: Modelo Gemini inicializado com sucesso.")
except Exception as e:
    model = None # Define model como None se houver erro
    print(f"ERRO CRÍTICO CHATBOT_UTILS_FINAL_V4: Não foi possível inicializar o modelo Gemini: {e}")
    traceback.print_exc()


def get_bot_response(user_message, chat_session):
    """
    Envia a mensagem do usuário para o chat_session do Gemini e retorna a resposta do bot.
    """
    if not model: # Verifica se o modelo foi inicializado
        return "Desculpe, o serviço de chat não está disponível no momento devido a um problema de configuração."
    if not chat_session: # Verifica se a sessão de chat é válida
        print("CHATBOT_UTILS_FINAL_V4_ERRO: chat_session é None em get_bot_response.")
        return "Desculpe, ocorreu um erro ao iniciar a sessão de chat."

    try:
        print(f"CHATBOT_UTILS_FINAL_V4: Enviando para Gemini: '{user_message[:100]}...'")
        response = chat_session.send_message(user_message)

        # Tratamento de resposta bloqueada ou sem candidatos
        if not response.candidates:
             print("CHATBOT_UTILS_FINAL_V4_WARN: Gemini não retornou candidatos.")
             block_reason_msg = "Não especificado"
             if response.prompt_feedback and response.prompt_feedback.block_reason:
                 block_reason_msg = getattr(response.prompt_feedback, 'block_reason_message', 'Motivo não especificado')
             current_app.logger.warning(f"Resposta do Gemini bloqueada (sem candidatos). Razão: {block_reason_msg}")
             return f"Desculpe, minha resposta foi bloqueada (Motivo: {block_reason_msg}). Poderia tentar reformular sua mensagem ou contactar o suporte se o problema persistir."

        candidate = response.candidates[0]

        # Log detalhado do finish_reason e safety_ratings
        finish_reason_value = getattr(candidate, 'finish_reason', 'UNKNOWN')
        print(f"CHATBOT_UTILS_FINAL_V4: Gemini respondeu. Finish reason: {finish_reason_value}")

        if candidate.finish_reason != 1: # 1 == genai.types.FinishReason.STOP
            reason_message = f"Motivo: {finish_reason_value}. "
            blocked_reason_msg_candidate = "Não especificado"
            if candidate.safety_ratings:
                reason_message += f"Safety Ratings: {[(r.category, r.probability, getattr(r, 'blocked', False)) for r in candidate.safety_ratings]}"
                for r_idx, r_val in enumerate(candidate.safety_ratings): # Usar r_idx, r_val
                    if getattr(r_val, 'blocked', False):
                        blocked_reason_msg_candidate = f"Bloqueio por {r_val.category}"
                        break
            print(f"CHATBOT_UTILS_FINAL_V4_WARN: Finish reason não foi STOP. {reason_message}")

            if candidate.finish_reason == 2: # 2 == genai.types.FinishReason.SAFETY
                 return f"Desculpe, minha resposta foi bloqueada por segurança (Detalhe: {blocked_reason_msg_candidate}). Poderia tentar uma pergunta ou frase diferente?"
            # Outros finish_reasons (MAX_TOKENS, RECITATION, OTHER)
            return "Houve um problema ao gerar a resposta completa, por favor, tente ser mais específico ou divida sua pergunta."

        # Extrai o texto da resposta
        if candidate.content and hasattr(candidate.content, 'parts') and candidate.content.parts:
            return "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
        elif hasattr(candidate, 'text') and candidate.text is not None: # Fallback para modelos mais antigos ou estruturas diferentes
            return candidate.text
        else:
            print("CHATBOT_UTILS_FINAL_V4_WARN: Resposta do Gemini não continha 'parts' com texto nem 'text' utilizável.")
            return "Desculpe, recebi uma resposta inesperada e não consigo processá-la."

    except Exception as e:
        error_str = str(e).lower()
        if hasattr(current_app, 'logger'): current_app.logger.error(f"Erro API Gemini em get_bot_response: {e}", exc_info=True)
        else: print(f"Erro (sem logger) API Gemini: {e}"); traceback.print_exc()

        if "quota" in error_str or "429" in error_str: return "Desculpe, o sistema atingiu o limite de interações por agora. Por favor, tente novamente mais tarde."

        # Trata StopCandidateException que pode vir com info de safety
        if isinstance(e, genai.types.StopCandidateException):
            if e.candidate and e.candidate.finish_reason == 2: # SAFETY
                 block_reason_msg = "Não especificado"
                 # Tenta obter a mensagem de bloqueio do prompt_feedback se disponível no erro
                 # A estrutura exata do erro pode variar.
                 if hasattr(e, '_response') and e._response and hasattr(e._response, 'prompt_feedback') and e._response.prompt_feedback and e._response.prompt_feedback.block_reason:
                     block_reason_msg = e._response.prompt_feedback.block_reason_message
                 elif e.candidate.safety_ratings: # Fallback para safety_ratings
                     for r_idx, r_val in enumerate(e.candidate.safety_ratings):
                         if getattr(r_val, 'blocked', False):
                             block_reason_msg = f"Bloqueio por {r_val.category}"
                             break
                 return f"Desculpe, minha tentativa de resposta foi bloqueada por segurança (Detalhe: {block_reason_msg}). Poderia tentar de outra forma?"

        if "safety" in error_str : return "Sua mensagem ou minha resposta foi bloqueada por segurança. Por favor, reformule."
        return "Desculpe, estou com um problema de conexão com o assistente. Tente novamente em alguns instantes."


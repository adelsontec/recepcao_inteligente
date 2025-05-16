import google.generativeai as genai
import os
from flask import current_app # Adicionado para logging

# print("====== MODULO CHATBOT_UTILS.PY (safety_fix_v2) CARREGADO ======") # Para depuração

try:
    api_k = os.getenv("GOOGLE_API_KEY")
    if not api_k:
        print("ALERTA: GOOGLE_API_KEY não encontrada no ambiente!")
    genai.configure(api_key=api_k)
except Exception as e:
    print(f"Erro GRAVE ao configurar a API Gemini. Verifique sua GOOGLE_API_KEY: {e}")

generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

# AJUSTE NOS SAFETY SETTINGS
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

SYSTEM_INSTRUCTION = f"""
Você é o CuidarBot, um assistente virtual amigável e eficiente do posto de saúde.
Sua principal missão é acolher os pacientes, perguntar qual o tipo de atendimento desejado (Exame, Consulta, Dentista ou Consulta Marcada), solicitar uma foto do documento de identificação, confirmar os dados extraídos e, finalmente, fornecer uma senha de atendimento sequencial e específica para a categoria escolhida.
Seja sempre gentil, paciente e use palavras positivas e motivadoras.
Fluxo da conversa:
1. Saudação inicial.
2. Pergunte: "Para qual tipo de atendimento você gostaria de gerar uma senha? Por favor, escolha entre: Exame, Consulta, Dentista ou Consulta Marcada."
3. Após o usuário escolher a categoria, confirme a categoria e peça a foto do documento (RG, CPF ou Carteirinha do SUS). Ex: "Entendido! Para seu atendimento de [CATEGORIA], por favor, envie a foto do seu documento."
4. Quando os dados do documento forem extraídos (Nome, CPF, RG, CNS), apresente-os para confirmação. Ex: "Do seu documento para [CATEGORIA], extraí: Nome: [NOME], CPF: [CPF], RG: [RG], CNS: [CNS]. Está tudo correto? Se algo estiver errado ou faltando, por favor, me diga."
5. Se o usuário confirmar, o sistema gerará a senha. Apresente a senha formatada (ex: "EXAME-001") e uma mensagem final encorajadora. Ex: "Perfeito! Sua senha para [CATEGORIA] é [SENHA_FORMATADA]. Aguarde com tranquilidade, logo será sua vez. Estamos aqui para cuidar de você!"
Evite informações médicas complexas ou diagnósticos.
Se o usuário fizer perguntas fora do escopo, gentilmente redirecione-o para o processo de atendimento.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    generation_config=generation_config,
    system_instruction=SYSTEM_INSTRUCTION,
    safety_settings=safety_settings
)

def get_bot_response(user_message, chat_session):
    try:
        print(f"CHATBOT_UTILS: Enviando para Gemini: '{user_message[:100]}...'")
        response = chat_session.send_message(user_message)

        if not response.candidates:
             print("CHATBOT_UTILS_WARN: Gemini não retornou candidatos. Finish reason:", response.prompt_feedback if response.prompt_feedback else "N/A")
             if response.prompt_feedback and response.prompt_feedback.block_reason:
                 return f"Desculpe, minha resposta foi bloqueada por segurança (Motivo: {response.prompt_feedback.block_reason_message}). Poderia tentar reformular?"
             return "Desculpe, não consegui gerar uma resposta no momento."

        print(f"CHATBOT_UTILS: Gemini respondeu. Finish reason: {response.candidates[0].finish_reason}")
        if response.candidates[0].finish_reason != 1: # 1 = STOP (normal)
            print(f"CHATBOT_UTILS_WARN: Finish reason não foi STOP. Detalhes: {response.candidates[0].safety_ratings}")
            if response.candidates[0].finish_reason == 2: # SAFETY
                 return f"Desculpe, minha resposta foi bloqueada por segurança. Poderia tentar uma pergunta diferente?"

        if response.parts:
            return "".join(part.text for part in response.parts if hasattr(part, 'text'))
        elif hasattr(response, 'text') and response.text is not None : # Verifica se response.text existe e não é None
            return response.text
        else:
            print("CHATBOT_UTILS_WARN: Resposta do Gemini não continha 'parts' com texto nem 'response.text' utilizável.")
            # CORREÇÃO DO SyntaxError:
            try: # Python usa ':' para iniciar um bloco try
                print(f"CHATBOT_UTILS_DEBUG: Resposta completa do Gemini (objeto): {response}")
                # Se quiser ver os atributos do objeto response:
                # print(f"CHATBOT_UTILS_DEBUG: Atributos de response: {dir(response)}")
            except Exception as log_e: # Python usa ':' para iniciar um bloco except
                print(f"CHATBOT_UTILS_DEBUG: Erro ao tentar logar resposta completa: {log_e}")
            return "Desculpe, recebi uma resposta inesperada e não consigo processá-la."

    except Exception as e:
        error_str = str(e).lower()
        if hasattr(current_app, 'logger'):
            current_app.logger.error(f"Erro ao comunicar com a API Gemini: {e}", exc_info=True)
        else:
            print(f"Erro (sem logger Flask) ao comunicar com a API Gemini: {e}")
            import traceback
            traceback.print_exc()

        if "quota" in error_str or "429" in error_str:
            return "Desculpe, parece que atingimos nosso limite de interações por agora. Por favor, tente novamente mais tarde. Agradecemos a compreensão!"
        if "safety" in error_str or (hasattr(e, 'response') and hasattr(e.response, 'prompt_feedback') and e.response.prompt_feedback and e.response.prompt_feedback.block_reason):
            return f"Desculpe, minha tentativa de resposta foi bloqueada por segurança (Motivo: {e.response.prompt_feedback.block_reason_message}). Poderia tentar de outra forma?"

        return "Desculpe, estou com um pequeno problema para me conectar agora. Tente novamente em instantes."


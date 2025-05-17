# app/chatbot_utils.py
import google.generativeai as genai
import os
from flask import current_app

try:
    api_k = os.getenv("GOOGLE_API_KEY")
    if not api_k: print("ALERTA CHATBOT_UTILS_FINAL_V3: GOOGLE_API_KEY não encontrada!")
    genai.configure(api_key=api_k)
except Exception as e:
    print(f"Erro CHATBOT_UTILS_FINAL_V3 ao configurar API Gemini: {e}")

generation_config = { "temperature": 0.7, "top_p": 0.95, "top_k": 40, "max_output_tokens": 2048 }
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

SYSTEM_INSTRUCTION = f"""
Você é o CuidarBot, um assistente virtual acolhedor e eficiente do posto de saúde.
Sua missão é facilitar a obtenção de uma senha de atendimento, focando em Nome, CPF e Data de Nascimento.

FLUXO PRINCIPAL (OCR):
1.  Após o usuário escolher a categoria, você pede o documento.
2.  Quando o sistema extrair dados (Nome, CPF, Data de Nascimento, Idade Calculada), você os apresenta para confirmação.
    Exemplo de prompt que você receberá do sistema: "Para [CATEGORIA], extraí: Nome: [NOME], CPF: [CPF], Data de Nascimento: [DATA_NASC], Idade Calculada: [IDADE]. Peça confirmação. Se não, instrua a dizer 'corrigir' ou 'digitar dados'."
    Sua resposta ao usuário deve ser algo como: "Consegui ler os seguintes dados do seu documento: Nome: [NOME], CPF: [CPF], Data de Nascimento: [DATA_NASC], Idade: [IDADE]. Está tudo correto? Se não, por favor, diga 'corrigir' para que possamos inserir os dados manualmente."
3.  Se o usuário confirmar ("sim"), o sistema gera a senha. Você a apresenta.
4.  Se o usuário disser 'corrigir' ou 'digitar dados', o sistema iniciará a coleta manual. O sistema te enviará um prompt para pedir o nome.

FLUXO DE COLETA MANUAL DE DADOS:
1.  **Pedido do Nome:** Se o sistema te enviar um prompt como "Não consegui ler todos os dados do seu documento. Vamos tentar inserir manualmente. Qual o seu nome completo?" OU "Entendido, vamos corrigir/inserir seus dados. Qual o seu nome completo?", faça essa pergunta claramente.
2.  **Pedido do CPF:** Após o usuário fornecer o nome, o sistema te enviará "Qual o seu CPF?". Pergunte o CPF. Se o usuário fornecer um CPF inválido e o sistema te disser "CPF inválido. Por favor, digite um CPF válido (ex: 123.456.789-00 ou 12345678900).", repita essa mensagem de erro e peça o CPF novamente.
3.  **Pedido da Data de Nascimento:** Após o CPF, o sistema te enviará "Qual a sua data de nascimento (DD/MM/AAAA)?". Pergunte. Se o formato for inválido e o sistema te disser "Formato de data inválido. Por favor, use DD/MM/AAAA.", repita a mensagem de erro e peça a data novamente.
4.  **Confirmação dos Dados Manuais:** Quando o sistema te enviar os dados coletados manualmente para confirmação (prompt: "Por favor, confirme os dados que você forneceu: Nome: [NOME], CPF: [CPF], Data de Nascimento: [DATA_NASC], Idade Calculada: [IDADE]. Está tudo correto? (Responda 'sim' ou 'não')"), apresente esses dados claramente e peça confirmação.
5.  **Após Confirmação Manual ("sim"):** O sistema gerará a senha. Você a apresenta como no fluxo normal. Se o usuário disser "não", o sistema te enviará um prompt para reiniciar o processo de envio de foto ou digitação.

OUTRAS SITUAÇÕES:
- **Senha Já Emitida:** Informe gentilmente.
- **Falha Geral no OCR (sem dados suficientes):** Se o sistema pedir para você dizer "Não consegui ler todos os dados do seu documento (Nome, CPF, Data de Nascimento). Vamos tentar inserir manualmente. Qual o seu nome completo?", diga isso para iniciar a coleta manual.

Mantenha sempre um tom positivo. Lembre ao usuário que a tela reiniciará em 10 segundos após a senha ser emitida.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    generation_config=generation_config,
    system_instruction=SYSTEM_INSTRUCTION,
    safety_settings=safety_settings
)

def get_bot_response(user_message, chat_session):
    # ... (Mantenha como na versão chatbot_utils_final_safety_fix)
    try:
        print(f"CHATBOT_UTILS_FINAL_V3: Enviando para Gemini: '{user_message[:100]}...'")
        response = chat_session.send_message(user_message)
        if not response.candidates:
             print("CHATBOT_UTILS_FINAL_V3_WARN: Gemini não retornou candidatos.")
             if response.prompt_feedback and response.prompt_feedback.block_reason:
                 return f"Desculpe, minha resposta foi bloqueada por segurança (Motivo: {getattr(response.prompt_feedback, 'block_reason_message', 'N/A')})."
             return "Desculpe, não consegui gerar uma resposta."
        candidate = response.candidates[0]
        print(f"CHATBOT_UTILS_FINAL_V3: Gemini respondeu. Finish reason: {candidate.finish_reason}")
        if candidate.finish_reason != 1:
            reason_message = f"Motivo: {candidate.finish_reason}. "
            if candidate.safety_ratings: reason_message += f"Safety: {[(r.category, r.probability, getattr(r, 'blocked', 'N/A')) for r in candidate.safety_ratings]}"
            print(f"CHATBOT_UTILS_FINAL_V3_WARN: Finish reason não foi STOP. {reason_message}")
            if candidate.finish_reason == 2: return f"Desculpe, minha resposta foi bloqueada por segurança."
            return "Houve um problema ao gerar a resposta."
        if candidate.content and hasattr(candidate.content, 'parts') and candidate.content.parts:
            return "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
        elif hasattr(candidate, 'text') and candidate.text is not None: return candidate.text
        elif hasattr(response, 'text') and response.text is not None : return response.text
        else: print("CHATBOT_UTILS_FINAL_V3_WARN: Resposta sem texto utilizável."); return "Resposta inesperada."
    except Exception as e:
        error_str = str(e).lower()
        if hasattr(current_app, 'logger'): current_app.logger.error(f"Erro API Gemini: {e}", exc_info=True)
        else: print(f"Erro (sem logger) API Gemini: {e}"); traceback.print_exc()
        if "quota" in error_str or "429" in error_str: return "Limite de interações atingido."
        if isinstance(e, genai.types.StopCandidateException):
            if e.candidate and e.candidate.finish_reason == 2: return f"Resposta bloqueada por segurança."
        if "safety" in error_str : return "Resposta bloqueada por segurança."
        return "Problema de conexão com o assistente."

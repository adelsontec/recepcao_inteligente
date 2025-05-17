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
Você é o CuidarBot, um assistente virtual extremamente acolhedor, paciente e eficiente do posto de saúde. Sua voz é calma, positiva e transmite segurança.
Sua missão principal é facilitar o processo de chegada dos pacientes, ajudando-os a obter uma senha de atendimento.

Siga este fluxo de interação com clareza e empatia:

1.  **Saudação Calorosa:** Cumprimente o paciente de forma amigável. Pergunte como ele está se sentindo hoje e ofereça uma breve palavra de conforto se ele parecer necessitar, antes de prosseguir. Ex: "Olá! Sou o CuidarBot, estou aqui para tornar sua chegada mais tranquila. Como você está se sentindo neste momento?"

2.  **Pergunta da Categoria:** De forma clara, pergunte para qual tipo de atendimento o paciente gostaria de gerar uma senha. Apresente as opções: "Exame", "Consulta", "Dentista" ou "Consulta Marcada". Ex: "Para que eu possa direcioná-lo(a) corretamente, qual o tipo de atendimento que você busca hoje? Temos senhas para Exame, Consulta, Dentista e Consulta Marcada."

3.  **Confirmação da Categoria e Pedido do Documento:** Após o paciente escolher a categoria, confirme a escolha e, de forma educada, peça para ele enviar uma foto de um documento de identificação com foto. Mencione que RG, CPF ou Carteirinha do SUS são aceites. Ex: "Entendido, atendimento para [CATEGORIA]! Para continuarmos, você poderia me enviar uma foto nítida do seu RG, CPF ou Carteirinha do SUS, por favor? Isso nos ajudará a agilizar seu cadastro."

4.  **Confirmação dos Dados Extraídos:** Quando o sistema extrair os dados do documento (Nome, CPF, RG, CNS, Data de Nascimento, Idade), apresente-os de forma organizada para o paciente confirmar. Seja explícito sobre quais dados foram encontrados e quais não. Ex: "Consegui ler algumas informações do seu documento para o atendimento de [CATEGORIA]: Nome: [NOME_EXTRAIDO], CPF: [CPF_EXTRAIDO ou 'Não encontrado'], RG: [RG_EXTRAIDO ou 'Não encontrado'], CNS: [CNS_EXTRAIDO ou 'Não encontrado'], Data de Nascimento: [DATA_NASC_EXTRAIDA ou 'Não encontrada'], Idade: [IDADE_CALCULADA ou 'Não calculada']. Por favor, verifique se está tudo correto. Se algo estiver diferente ou faltando, é só me dizer!"

5.  **Geração e Apresentação da Senha:** Se o paciente confirmar os dados, o sistema gerará a senha. Apresente a senha de forma clara (ex: "EXAME - E-001") e adicione uma mensagem final positiva e encorajadora, reforçando que a equipa está pronta para ajudar. Ex: "Perfeito, [NOME DO PACIENTE]! Sua senha para [CATEGORIA] é [SENHA_FORMATADA]. Por favor, guarde este número. Logo você será chamado(a). Enquanto aguarda, saiba que estamos aqui para cuidar de você e desejamos que se sinta melhor em breve!"

6.  **Caso de Senha Já Emitida:** Se o sistema identificar que o paciente (pelo CPF) já retirou uma senha para qualquer categoria no dia atual, informe-o de forma clara e gentil, mencionando a senha e a categoria já emitidas, e explicando a política de uma senha por dia. Ex: "Verifiquei aqui, [NOME DO PACIENTE], e você já possui a senha [SENHA_EXISTENTE] para o atendimento de [CATEGORIA_EXISTENTE] emitida hoje. Só é permitida uma senha por dia, independentemente da categoria. Por favor, aguarde ser chamado(a) ou, se houver alguma questão, dirija-se ao balcão de informações. Obrigado pela compreensão!"

7.  **Falha no OCR:** Se o sistema não conseguir ler o documento, peça gentilmente para o paciente tentar novamente com uma foto melhor. Ex: "Peço desculpas, mas não consegui ler as informações do seu documento claramente. Você poderia tentar enviar uma nova foto, por favor? Procure um local bem iluminado e certifique-se de que a imagem está nítida e sem cortes."

Mantenha sempre um tom positivo e de apoio. Evite informações médicas complexas ou diagnósticos. Se o utilizador fizer perguntas fora do escopo da recepção, redirecione-o gentilmente para aguardar o atendimento profissional ou procurar o balcão de informações.
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


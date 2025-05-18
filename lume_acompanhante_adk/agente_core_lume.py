# lume_acompanhante_adk/agente_core_lume.py
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

import warnings
import traceback
import re
import time

warnings.filterwarnings("ignore")

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

print("MODULO AGENTE_CORE_LUME (v10.Final - Compatível com Rotas) CARREGADO")

# --- Configuração da API Key ---
api_key = os.getenv("GOOGLE_API_KEY_LUME") or os.getenv("GOOGLE_API_KEY")
if api_key:
    try:
        from google import genai
        genai.configure(api_key=api_key)
        print("AGENTE_CORE_LUME: API Key do Google Gemini configurada.")
    except AttributeError:
        print("AGENTE_CORE_LUME: Atributo 'configure' não encontrado. ADK usará var de ambiente.")
    except Exception as e:
        print(f"AGENTE_CORE_LUME: Erro ao configurar genai: {e}")
else:
    print("ALERTA CRÍTICO AGENTE_CORE_LUME: Nenhuma GOOGLE_API_KEY encontrada.")

# --- Função Auxiliar call_agent ---
def call_agent(agent: Agent, message_text: str, session_id: str = "lume_sess_default", user_id: str = "lume_user_default") -> str:
    print(f"\n[Chamando Agente ADK: {agent.name} (Sessão: {session_id}, Utilizador: {user_id})]")
    print(f"  -> Input para {agent.name}: {message_text[:200]}...")
    session_service = InMemorySessionService()
    adk_session_obj = session_service.create_session(app_name=agent.name, user_id=user_id, session_id=session_id)
    runner = Runner(agent=agent, app_name=agent.name, session_service=session_service)
    content = genai_types.Content(role="user", parts=[genai_types.Part(text=message_text)])
    final_response_parts = []
    try:
        for event in runner.run(user_id=user_id, session_id=adk_session_obj.id, new_message=content):
            if event.is_final_response():
                if event.content and hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text is not None:
                            final_response_parts.append(part.text)
                elif hasattr(event, 'text') and event.text is not None:
                     final_response_parts.append(event.text)
    except Exception as e:
        print(f"Erro durante a execução do agente {agent.name}: {e}"); traceback.print_exc()
        return f"Desculpe, o Agente {agent.name} encontrou um problema."
    final_response = "\n".join(final_response_parts).strip()
    print(f"  <- {agent.name} respondeu: {final_response[:200]}...")
    return final_response

# --- Agente 1: Lume (Acolhedora) ---
def criar_agente_lume():
    instrucoes_lume = """
    Você é a Lume, uma presença acolhedora, gentil e positiva. Sua missão é criar uma conexão humana e leve.
    Você está sempre aprendendo!

    FLUXO DA CONVERSA INICIAL:
    1.  SE O INPUT DO USUÁRIO FOR UMA SAUDAÇÃO INICIAL (ex: "Olá!", "Oi Lume"):
        Responda cumprimentando com doçura e PERGUNTE O NOME do usuário.
        Exemplo de sua resposta: "Oi! 😊 Que bom ter você aqui. Para começarmos, me conta, como você se chama?"
    2.  SE O INPUT DO USUÁRIO PARECER SER UM NOME (ex: "Meu nome é Adelson", ou apenas "Adelson", ou o orquestrador enviar um prompt como "Contexto: O usuário disse que se chama Adelson."):
        Use o nome que foi fornecido (que estará no input ou no histórico da conversa), demonstre simpatia e PERGUNTE COMO ELE ESTÁ SE SENTINDO.
        Exemplo de sua resposta: "Prazer em te conhecer, Adelson! Como você está se sentindo nesse momento?"
    3.  SE O INPUT DO USUÁRIO FOR UMA DESCRIÇÃO DE COMO ELE ESTÁ SE SENTINDO (ex: "Estou bem", "um pouco ansioso", ou o orquestrador enviar um prompt como "Contexto: O usuário Adelson disse que está se sentindo 'um pouco ansioso'."):
        Use o nome (se souber do histórico), agradeça por compartilhar. Ofereça companhia e SUGIRA levemente opções como uma curiosidade, uma dica de relaxamento ou palavras de ânimo.
        Exemplo de sua resposta: "Entendo, Adelson. Obrigado por compartilhar. Se quiser, posso te contar uma curiosidade, te guiar numa respiração relaxante, ou apenas bater um papo leve. O que te parece mais agradável agora?"

    PARA OUTRAS INTERAÇÕES (APÓS O FLUXO INICIAL):
    - Se a pessoa pedir algo específico (relaxamento, curiosidade, etc.), responda de forma afirmativa e encorajadora. Ex: "Claro! Uma dica de relaxamento pode ser ótima." (O sistema externo chamará o especialista).
    - Se o usuário continuar uma conversa geral, responda de forma empática e positiva. Lembre-se do nome do usuário se ele já o forneceu.
    - Se não souber responder a algo muito específico, pode dizer que está aprendendo.
    - Nunca dê conselhos médicos. Seja breve e simpática. Use emojis com moderação 🌿.
    """
    agente = Agent(name="Lume", model="gemini-1.5-flash-latest", instruction=instrucoes_lume)
    print("Agente Lume (v10.Final) criado.")
    return agente

# --- Agentes Especialistas (Mantenha os 3 que você escolheu) ---
def criar_agente_relaxamento():
    instrucoes = "Você é um Guia de Relaxamento. Guie uma técnica de respiração curta ou dê uma dica de relaxamento rápido."
    return Agent(name="AgenteDeRelaxamento", model="gemini-1.5-flash-latest", instruction=instrucoes)
def criar_agente_espiritual_motivacional():
    instrucoes = "Você é um Conselheiro Espiritual. Compartilhe um versículo positivo, ou uma frase de fé/ânimo."
    return Agent(name="AgenteEspiritualMotivacional", model="gemini-1.5-flash-latest", instruction=instrucoes)
def criar_agente_curiosidades():
    instrucoes = "Você é um Curioso Sabichão. Compartilhe uma curiosidade leve e interessante."
    return Agent(name="AgenteDeCuriosidadesLeves", model="gemini-1.5-flash-latest", instruction=instrucoes)

# --- Dicionário de Roteamento ---
roteamento_palavras_chave = {
    "relaxar": "AgenteDeRelaxamento", "ansioso": "AgenteDeRelaxamento", "respiração": "AgenteDeRelaxamento", "calma": "AgenteDeRelaxamento",
    "fé": "AgenteEspiritualMotivacional", "motivação": "AgenteEspiritualMotivacional", "ânimo": "AgenteEspiritualMotivacional", "versículo": "AgenteEspiritualMotivacional", "triste": "AgenteEspiritualMotivacional",
    "curiosidade": "AgenteDeCuriosidadesLeves", "fato": "AgenteDeCuriosidadesLeves", "interessante": "AgenteDeCuriosidadesLeves",
}

def rotear_para_especialista(resposta_usuario: str, agentes_especialistas: dict):
    for palavra, nome_agente_destino in roteamento_palavras_chave.items():
        if palavra in resposta_usuario.lower():
            if nome_agente_destino in agentes_especialistas:
                return nome_agente_destino, palavra
    return None, None

# --- Ponto de Entrada para Flask ---
agente_lume_global = None
agentes_especialistas_globais = {}

def inicializar_agentes_lume():
    global agente_lume_global, agentes_especialistas_globais
    if not agente_lume_global:
        agente_lume_global = criar_agente_lume()
        agentes_especialistas_globais = {
            "AgenteDeRelaxamento": criar_agente_relaxamento(),
            "AgenteEspiritualMotivacional": criar_agente_espiritual_motivacional(),
            "AgenteDeCuriosidadesLeves": criar_agente_curiosidades(),
        }
        print("AGENTES PARA LUME (v10.Final Core) INICIALIZADOS")

# Esta é a função que será chamada pelo Flask
def interagir_com_lume_e_rotear(mensagem_usuario: str, estado_conversa_atual: dict, user_id: str):
    inicializar_agentes_lume() # Garante que estão criados
    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY_LUME")):
        return "Erro: API Key não configurada.", estado_conversa_atual

    novo_estado_conversa = estado_conversa_atual.copy()
    sessao_id_adk_lume = f"{user_id}_lume_chat_v10_final"
    prompt_para_lume = mensagem_usuario
    resposta_final_para_usuario = ""

    print(f"LUME_CORE (interagir_v10.Final): Estado ANTES: {novo_estado_conversa}, User Msg: {mensagem_usuario}")
    etapa = novo_estado_conversa.get("etapa_conversa", "inicio")

    if etapa == "inicio":
        resposta_lume = call_agent(agente_lume_global, prompt_para_lume, session_id=sessao_id_adk_lume, user_id=user_id)
        if "como você se chama" in resposta_lume.lower() or "qual o seu nome" in resposta_lume.lower():
            novo_estado_conversa["etapa_conversa"] = "esperando_nome"
        resposta_final_para_usuario = resposta_lume
    elif etapa == "esperando_nome":
        novo_estado_conversa["nome_usuario"] = mensagem_usuario
        prompt_para_lume = f"Contexto: Meu nome é {novo_estado_conversa['nome_usuario']}."
        resposta_lume = call_agent(agente_lume_global, prompt_para_lume, session_id=sessao_id_adk_lume, user_id=user_id)
        if "como você está se sentindo" in resposta_lume.lower():
            novo_estado_conversa["etapa_conversa"] = "esperando_sentimento"
        resposta_final_para_usuario = resposta_lume
    elif etapa == "esperando_sentimento":
        sentimento_usuario = mensagem_usuario
        novo_estado_conversa["sentimento_previo"] = sentimento_usuario
        nome_usr = novo_estado_conversa.get("nome_usuario", "você")
        prompt_para_lume = f"Contexto: Eu ({nome_usr}) estou me sentindo '{sentimento_usuario}'."
        resposta_lume = call_agent(agente_lume_global, prompt_para_lume, session_id=sessao_id_adk_lume, user_id=user_id)
        if any(sug in resposta_lume.lower() for sug in ["curiosidade", "relaxante", "ânimo", "dica", "sugestão"]):
            novo_estado_conversa["etapa_conversa"] = "conversa_aberta"
        resposta_final_para_usuario = resposta_lume
    elif etapa == "conversa_aberta":
        nome_agente_especialista, palavra_chave = rotear_para_especialista(mensagem_usuario, agentes_especialistas_globais)
        if nome_agente_especialista:
            agente_a_chamar = agentes_especialistas_globais[nome_agente_especialista]
            nome_usr = novo_estado_conversa.get("nome_usuario", "O usuário")
            prompt_especialista = f"{nome_usr} pediu ajuda com '{palavra_chave}'."
            resposta_especialista = call_agent(agente_a_chamar, prompt_especialista, session_id=f"{user_id}_{nome_agente_especialista}", user_id=user_id)
            prompt_lume_pos_especialista = f"Contexto: Dei uma dica sobre {palavra_chave} para {nome_usr}. Pergunte se ajudou e se ele quer mais alguma coisa."
            resposta_lume_final = call_agent(agente_lume_global, prompt_lume_pos_especialista, session_id=sessao_id_adk_lume, user_id=user_id)
            resposta_final_para_usuario = f"{resposta_especialista}\n\n{resposta_lume_final}"
        else:
            nome_usr = novo_estado_conversa.get("nome_usuario", "o usuário")
            sentimento_usr = novo_estado_conversa.get("sentimento_previo", "não especificado")
            prompt_lume_geral = (f"Contexto: Conversando com {nome_usr} (sentimento: '{sentimento_usr}'). Mensagem: '{mensagem_usuario}'. Continue.")
            resposta_final_para_usuario = call_agent(agente_lume_global, prompt_lume_geral, session_id=sessao_id_adk_lume, user_id=user_id)
    else:
        novo_estado_conversa["etapa_conversa"] = "inicio"; novo_estado_conversa["nome_usuario"] = None; novo_estado_conversa["sentimento_previo"] = None
        resposta_final_para_usuario = call_agent(agente_lume_global, "Olá, podemos recomeçar?", session_id=sessao_id_adk_lume, user_id=user_id)

    print(f"LUME_CORE (interagir_v10.Final): Estado DEPOIS: {novo_estado_conversa}")
    return resposta_final_para_usuario, novo_estado_conversa

inicializar_agentes_lume()

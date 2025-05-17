# app/db_utils.py
import sqlite3
from datetime import date
import os
import traceback

print("DB_UTILS: Modulo carregado (v_final_com_idade_e_limite_geral)")

DATABASE_NAME = 'credentials.db' # O arquivo do banco será criado na raiz do projeto

def get_db_connection():
    """Estabelece conexão com o banco de dados SQLite."""
    # print("DB_UTILS: Tentando conectar ao banco de dados...") # Pode ser muito verboso
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    # print("DB_UTILS: Conexão com o banco estabelecida.")
    return conn

def init_db():
    """Inicializa o banco de dados criando as tabelas a partir do schema.sql."""
    print("DB_UTILS: Entrou em init_db()")
    conn = None
    try:
        conn = get_db_connection()
        print("DB_UTILS: Conexão obtida para init_db.")
        # Constrói o caminho para schema.sql relativo à localização de db_utils.py
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        print(f"DB_UTILS: Tentando abrir schema.sql em: {schema_path}")

        with open(schema_path, 'r') as f:
            schema_content = f.read()
            print("DB_UTILS: Conteúdo do schema.sql lido.")
            conn.executescript(schema_content)
        print("DB_UTILS: Banco de dados inicializado com sucesso com o schema.")
    except sqlite3.Error as e:
        print(f"DB_UTILS_ERRO: Erro SQLite ao inicializar o banco: {e}")
    except FileNotFoundError:
        print(f"DB_UTILS_ERRO: Arquivo schema.sql não encontrado em '{schema_path}'. Verifique o caminho.")
    except Exception as e_geral:
        print(f"DB_UTILS_ERRO: Erro geral ao inicializar o banco: {e_geral}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
            print("DB_UTILS: Conexão com o banco fechada em init_db.")

def check_existing_ticket_overall(cpf, data_hoje_str):
    """
    Verifica se já existe QUALQUER senha para este CPF na data especificada.
    Retorna um dicionário {'senha_formatada': ..., 'categoria_atendimento': ...} se encontrada, senão None.
    """
    if not cpf: # Não podemos verificar sem CPF
        print("DB_UTILS_CHECK_TICKET: CPF não fornecido para verificação.")
        return None

    conn = get_db_connection()
    cursor = conn.cursor()
    print(f"DB_UTILS_CHECK_TICKET: Verificando QUALQUER senha existente para CPF: {cpf}, Data: {data_hoje_str}")

    cursor.execute(
        """SELECT senha_formatada, categoria_atendimento FROM visitantes
           WHERE cpf = ? AND date(horario_entrada) = ?
           ORDER BY horario_entrada DESC LIMIT 1""",
        (cpf, data_hoje_str)
    )
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        print(f"DB_UTILS_CHECK_TICKET: Senha existente encontrada: {resultado['senha_formatada']} para Categoria: {resultado['categoria_atendimento']}")
        return {'senha_formatada': resultado['senha_formatada'], 'categoria_atendimento': resultado['categoria_atendimento']}
    print("DB_UTILS_CHECK_TICKET: Nenhuma senha existente encontrada para este CPF hoje.")
    return None

def get_next_senha_for_category(categoria_atendimento):
    """
    Gera a próxima senha sequencial para uma categoria, reiniciando diariamente.
    """
    print(f"DB_UTILS_GET_SENHA: Entrou para categoria: {categoria_atendimento}")
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hoje_str = date.today().isoformat()
        print(f"DB_UTILS_GET_SENHA: Data de hoje para senha: {hoje_str}")

        cursor.execute(
            "SELECT ultimo_numero_senha FROM contadores_senhas_diarias WHERE data_atendimento = ? AND categoria = ?",
            (hoje_str, categoria_atendimento.upper())
        )
        resultado = cursor.fetchone()
        print(f"DB_UTILS_GET_SENHA: Resultado da consulta por contador existente: {resultado}")

        if resultado:
            proximo_numero = resultado['ultimo_numero_senha'] + 1
            print(f"DB_UTILS_GET_SENHA: Contador existente. Próximo número: {proximo_numero}")
            cursor.execute(
                "UPDATE contadores_senhas_diarias SET ultimo_numero_senha = ? WHERE data_atendimento = ? AND categoria = ?",
                (proximo_numero, hoje_str, categoria_atendimento.upper())
            )
            print(f"DB_UTILS_GET_SENHA: Contador atualizado para {proximo_numero}.")
        else:
            proximo_numero = 1
            print(f"DB_UTILS_GET_SENHA: Novo contador para categoria/data. Próximo número: {proximo_numero}")
            cursor.execute(
                "INSERT INTO contadores_senhas_diarias (data_atendimento, categoria, ultimo_numero_senha) VALUES (?, ?, ?)",
                (hoje_str, categoria_atendimento.upper(), proximo_numero)
            )
            print(f"DB_UTILS_GET_SENHA: Novo contador inserido.")

        conn.commit()
        print("DB_UTILS_GET_SENHA: Commit da transação de senha realizado.")

        prefixo_map = {"EXAME": "E", "CONSULTA": "C", "DENTISTA": "D", "CONSULTA MARCADA": "CM"}
        prefixo = prefixo_map.get(categoria_atendimento.upper(), "GERAL")
        senha_formatada = f"{prefixo}-{proximo_numero:03d}"
        print(f"DB_UTILS_GET_SENHA: Senha gerada para {categoria_atendimento} em {hoje_str}: {senha_formatada}")
        return senha_formatada
    except sqlite3.Error as e:
        print(f"DB_UTILS_ERRO: Erro SQLite em get_next_senha_for_category: {e}")
        return None
    except Exception as e_geral:
        print(f"DB_UTILS_ERRO: Erro geral em get_next_senha_for_category: {e_geral}")
        traceback.print_exc()
        return None
    finally:
        if conn:
            conn.close()
            # print(f"DB_UTILS_GET_SENHA: Conexão com o banco fechada.") # Pode ser muito verboso

def add_visitor(nome, cpf, rg, cns, foto_path, categoria_atendimento, senha_formatada,
                data_nascimento, idade, horario_entrada):
    """Adiciona um novo visitante ao banco de dados."""
    conn = None
    try:
        conn = get_db_connection()
        print(f"DB_UTILS_ADD_VISITOR: Adicionando: Nome={nome}, CPF={cpf}, RG={rg}, CNS={cns}, DN={data_nascimento}, Idade={idade}, Cat={categoria_atendimento}, Senha={senha_formatada}")
        conn.execute(
            'INSERT INTO visitantes (nome, cpf, rg, cns, foto_path, categoria_atendimento, senha_formatada, data_nascimento, idade, horario_entrada) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (nome, cpf, rg, cns, foto_path, categoria_atendimento.upper(), senha_formatada, data_nascimento, idade, horario_entrada)
        )
        conn.commit()
        print(f"DB_UTILS_ADD_VISITOR: Visitante adicionado com sucesso: {nome}")
    except sqlite3.Error as e:
        print(f"DB_UTILS_ERRO: Erro SQLite ao adicionar visitante '{nome}': {e}")
    except Exception as e_geral:
        print(f"DB_UTILS_ERRO: Erro geral ao adicionar visitante '{nome}': {e_geral}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
            # print(f"DB_UTILS_ADD_VISITOR: Conexão com o banco fechada.") # Pode ser muito verboso

def get_todays_visitors():
    """Busca todos os visitantes registrados no dia atual."""
    conn = get_db_connection()
    cursor = conn.cursor()
    hoje_str = date.today().isoformat()
    print(f"DB_UTILS_ADMIN: Buscando visitantes para a data: {hoje_str}")
    cursor.execute(
        """SELECT id, nome, cpf, rg, cns, categoria_atendimento, senha_formatada, data_nascimento, idade, horario_entrada
           FROM visitantes
           WHERE date(horario_entrada) = ?
           ORDER BY categoria_atendimento, datetime(horario_entrada) ASC""",
        (hoje_str,)
    )
    visitantes_rows = cursor.fetchall()
    conn.close()
    visitantes = [dict(row) for row in visitantes_rows] # Converte para lista de dicionários
    print(f"DB_UTILS_ADMIN: Encontrados {len(visitantes)} visitantes para hoje.")
    return visitantes

def delete_visitor_by_id(visitor_id):
    """Apaga um visitante do banco de dados pelo seu ID."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print(f"DB_UTILS_DELETE: Tentando apagar visitante com ID: {visitor_id}")
        cursor.execute("DELETE FROM visitantes WHERE id = ?", (visitor_id,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"DB_UTILS_DELETE: Visitante com ID {visitor_id} apagado com sucesso.")
            return True
        else:
            print(f"DB_UTILS_DELETE: Nenhum visitante encontrado com ID {visitor_id} para apagar.")
            return False
    except sqlite3.Error as e:
        print(f"DB_UTILS_DELETE_ERRO: Erro SQLite ao apagar visitante ID {visitor_id}: {e}")
        return False
    except Exception as e_geral:
        print(f"DB_UTILS_DELETE_ERRO: Erro geral ao apagar visitante ID {visitor_id}: {e_geral}")
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()

# app/db_utils.py
import sqlite3
from datetime import date
import os
import traceback

# Mantenha o print da versão do seu módulo aqui para depuração
print("DB_UTILS: Modulo carregado (com visualização admin e limite 1 senha por DIA GERAL)")

DATABASE_NAME = 'credentials.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = None
    try:
        conn = get_db_connection()
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_content = f.read()
            conn.executescript(schema_content)
        print("DB_UTILS: Banco de dados inicializado com sucesso com o schema.")
    except sqlite3.Error as e:
        print(f"DB_UTILS_ERRO: Erro SQLite ao inicializar o banco: {e}")
    except FileNotFoundError:
        print(f"DB_UTILS_ERRO: Arquivo schema.sql não encontrado em '{schema_path}'.")
    except Exception as e_geral:
        print(f"DB_UTILS_ERRO: Erro geral ao inicializar o banco: {e_geral}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

def check_existing_ticket_overall(cpf, data_hoje_str):
    if not cpf:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    print(f"DB_UTILS: Verificando QUALQUER senha existente para CPF: {cpf}, Data: {data_hoje_str}")
    cursor.execute(
        """SELECT senha_formatada, categoria_atendimento FROM visitantes
           WHERE cpf = ? AND date(horario_entrada) = ?
           ORDER BY horario_entrada DESC LIMIT 1""",
        (cpf, data_hoje_str)
    )
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        print(f"DB_UTILS: Senha existente encontrada: {resultado['senha_formatada']} para Categoria: {resultado['categoria_atendimento']}")
        return {'senha_formatada': resultado['senha_formatada'], 'categoria_atendimento': resultado['categoria_atendimento']}
    print("DB_UTILS: Nenhuma senha existente encontrada para este CPF hoje.")
    return None

def get_next_senha_for_category(categoria_atendimento):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hoje_str = date.today().isoformat()
        cursor.execute(
            "SELECT ultimo_numero_senha FROM contadores_senhas_diarias WHERE data_atendimento = ? AND categoria = ?",
            (hoje_str, categoria_atendimento.upper())
        )
        resultado = cursor.fetchone()
        if resultado:
            proximo_numero = resultado['ultimo_numero_senha'] + 1
            cursor.execute(
                "UPDATE contadores_senhas_diarias SET ultimo_numero_senha = ? WHERE data_atendimento = ? AND categoria = ?",
                (proximo_numero, hoje_str, categoria_atendimento.upper())
            )
        else:
            proximo_numero = 1
            cursor.execute(
                "INSERT INTO contadores_senhas_diarias (data_atendimento, categoria, ultimo_numero_senha) VALUES (?, ?, ?)",
                (hoje_str, categoria_atendimento.upper(), proximo_numero)
            )
        conn.commit()
        prefixo_map = {"EXAME": "E", "CONSULTA": "C", "DENTISTA": "D", "CONSULTA MARCADA": "CM"}
        prefixo = prefixo_map.get(categoria_atendimento.upper(), "GERAL")
        senha_formatada = f"{prefixo}-{proximo_numero:03d}"
        print(f"DB_UTILS: Senha gerada para {categoria_atendimento} em {hoje_str}: {senha_formatada}")
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

def add_visitor(nome, cpf, rg, cns, foto_path, categoria_atendimento, senha_formatada, horario_entrada):
    conn = None
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO visitantes (nome, cpf, rg, cns, foto_path, categoria_atendimento, senha_formatada, horario_entrada) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (nome, cpf, rg, cns, foto_path, categoria_atendimento.upper(), senha_formatada, horario_entrada)
        )
        conn.commit()
        print(f"DB_UTILS: Visitante adicionado com sucesso: {nome}")
    except sqlite3.Error as e:
        print(f"DB_UTILS_ERRO: Erro SQLite ao adicionar visitante '{nome}': {e}")
    except Exception as e_geral:
        print(f"DB_UTILS_ERRO: Erro geral ao adicionar visitante '{nome}': {e_geral}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

def get_todays_visitors():
    """Busca todos os visitantes registrados no dia atual."""
    conn = get_db_connection()
    cursor = conn.cursor()
    hoje_str = date.today().isoformat()
    print(f"DB_UTILS_ADMIN: Buscando visitantes para a data: {hoje_str}")
    cursor.execute(
        """SELECT nome, cpf, rg, cns, categoria_atendimento, senha_formatada, horario_entrada
           FROM visitantes
           WHERE date(horario_entrada) = ?
           ORDER BY categoria_atendimento, datetime(horario_entrada) ASC""", # Ordena pela hora exata
        (hoje_str,)
    )
    visitantes = cursor.fetchall() # Retorna uma lista de objetos sqlite3.Row
    conn.close()
    print(f"DB_UTILS_ADMIN: Encontrados {len(visitantes)} visitantes para hoje.")
    # Converte sqlite3.Row para dicionários para facilitar o uso no template
    return [dict(row) for row in visitantes]

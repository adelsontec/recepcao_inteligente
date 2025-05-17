# Versão final do projeto CuidarBot para Imersão IA Alura+Google
# app/db_utils.py
import sqlite3
from datetime import date
import os
import traceback

print("DB_UTILS: Modulo carregado (FINAL - Nome, CPF, DN)")

DATABASE_NAME = 'credentials.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    print("DB_UTILS: Entrou em init_db()")
    conn = None
    try:
        conn = get_db_connection()
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_content = f.read()
            conn.executescript(schema_content)
        print("DB_UTILS: Banco de dados inicializado com sucesso com o schema (FINAL).")
    except Exception as e_geral:
        print(f"DB_UTILS_ERRO: Erro geral ao inicializar o banco: {e_geral}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

def check_existing_ticket_overall(cpf, data_hoje_str):
    if not cpf: return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT senha_formatada, categoria_atendimento FROM visitantes
           WHERE cpf = ? AND date(horario_entrada) = ?
           ORDER BY horario_entrada DESC LIMIT 1""",
        (cpf, data_hoje_str)
    )
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        return {'senha_formatada': resultado['senha_formatada'], 'categoria_atendimento': resultado['categoria_atendimento']}
    return None

def get_next_senha_for_category(categoria_atendimento):
    # ... (Mantenha como na v_final_com_idade_e_limite_geral)
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
        return senha_formatada
    except Exception as e_geral:
        print(f"DB_UTILS_ERRO: Erro geral em get_next_senha_for_category: {e_geral}")
        traceback.print_exc()
        return None
    finally:
        if conn: conn.close()

# --- ATUALIZAR add_visitor ---
def add_visitor(nome, cpf, foto_path, categoria_atendimento, senha_formatada,
                data_nascimento, idade, horario_entrada): # Removidos rg e cns
    conn = None
    try:
        conn = get_db_connection()
        print(f"DB_UTILS_ADD_VISITOR (FINAL): Adicionando: Nome={nome}, CPF={cpf}, DN={data_nascimento}, Idade={idade}, Cat={categoria_atendimento}, Senha={senha_formatada}")
        conn.execute(
            # Query SQL atualizada para não incluir rg e cns
            'INSERT INTO visitantes (nome, cpf, foto_path, categoria_atendimento, senha_formatada, data_nascimento, idade, horario_entrada) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (nome, cpf, foto_path, categoria_atendimento.upper(), senha_formatada, data_nascimento, idade, horario_entrada)
        )
        conn.commit()
        print(f"DB_UTILS_ADD_VISITOR (FINAL): Visitante adicionado com sucesso: {nome}")
    except Exception as e_geral:
        print(f"DB_UTILS_ERRO: Erro geral ao adicionar visitante '{nome}': {e_geral}")
        traceback.print_exc()
    finally:
        if conn: conn.close()

# --- ATUALIZAR get_todays_visitors ---
def get_todays_visitors():
    conn = get_db_connection()
    cursor = conn.cursor()
    hoje_str = date.today().isoformat()
    print(f"DB_UTILS_ADMIN (FINAL): Buscando visitantes para a data: {hoje_str}")
    cursor.execute(
        # Query SQL atualizada para não incluir rg e cns
        """SELECT id, nome, cpf, categoria_atendimento, senha_formatada, data_nascimento, idade, horario_entrada
           FROM visitantes
           WHERE date(horario_entrada) = ?
           ORDER BY categoria_atendimento, datetime(horario_entrada) ASC""",
        (hoje_str,)
    )
    visitantes_rows = cursor.fetchall()
    conn.close()
    visitantes = [dict(row) for row in visitantes_rows]
    print(f"DB_UTILS_ADMIN (FINAL): Encontrados {len(visitantes)} visitantes para hoje.")
    return visitantes

def delete_visitor_by_id(visitor_id):
    # ... (Mantenha como na v_final_com_idade_e_limite_geral)
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
    except Exception as e_geral:
        print(f"DB_UTILS_DELETE_ERRO: Erro geral ao apagar visitante ID {visitor_id}: {e_geral}")
        traceback.print_exc()
        return False
    finally:
        if conn: conn.close()

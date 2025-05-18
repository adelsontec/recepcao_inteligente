-- app/schema.sql

DROP TABLE IF EXISTS visitantes;
DROP TABLE IF EXISTS contadores_senhas_diarias;

-- Tabela para armazenar informações dos visitantes e suas senhas
CREATE TABLE visitantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cpf TEXT,
    -- rg TEXT, -- Removido
    -- cns TEXT, -- Removido
    foto_path TEXT, -- Mantido para o caso de OCR bem-sucedido
    categoria_atendimento TEXT NOT NULL,
    senha_formatada TEXT NOT NULL,
    data_nascimento TEXT,
    idade INTEGER,
    horario_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para gerenciar os contadores diários de senhas por categoria
CREATE TABLE contadores_senhas_diarias (
    data_atendimento TEXT NOT NULL,
    categoria TEXT NOT NULL,
    ultimo_numero_senha INTEGER NOT NULL,
    PRIMARY KEY (data_atendimento, categoria)
);

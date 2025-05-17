-- app/schema.sql

-- Apaga as tabelas se elas já existirem, para garantir um estado limpo ao inicializar
DROP TABLE IF EXISTS visitantes;
DROP TABLE IF EXISTS contadores_senhas_diarias;

-- Tabela para armazenar informações dos visitantes e suas senhas
CREATE TABLE visitantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,       -- Identificador único para cada registo
    nome TEXT,                                  -- Nome do visitante extraído do OCR
    cpf TEXT,                                   -- CPF do visitante (pode ser usado como identificador único por dia)
    rg TEXT,                                    -- RG do visitante
    cns TEXT,                                   -- Número do Cartão Nacional de Saúde (Cartão SUS)
    foto_path TEXT,                             -- Caminho para a imagem do documento enviada (opcional)
    categoria_atendimento TEXT NOT NULL,        -- Categoria escolhida (Exame, Consulta, etc.)
    senha_formatada TEXT NOT NULL,              -- Senha gerada (ex: E-001, C-002)
    data_nascimento TEXT,                       -- Data de nascimento extraída (formato DD/MM/YYYY ou YYYY-MM-DD)
    idade INTEGER,                              -- Idade calculada
    horario_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Data e hora em que a senha foi gerada
);

-- Tabela para gerenciar os contadores diários de senhas por categoria
CREATE TABLE contadores_senhas_diarias (
    data_atendimento TEXT NOT NULL,         -- Data no formato 'YYYY-MM-DD'
    categoria TEXT NOT NULL,                -- Categoria do atendimento (EXAME, CONSULTA, etc.)
    ultimo_numero_senha INTEGER NOT NULL,   -- Último número de senha emitido para essa categoria nesse dia
    PRIMARY KEY (data_atendimento, categoria) -- Garante que cada categoria tenha apenas um contador por dia
);

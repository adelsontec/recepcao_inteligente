        DROP TABLE IF EXISTS visitantes;
        CREATE TABLE visitantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cpf TEXT,
            rg TEXT,
            cns TEXT,
            foto_path TEXT,
            categoria_atendimento TEXT NOT NULL,
            senha_formatada TEXT NOT NULL,
            horario_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        DROP TABLE IF EXISTS contadores_senhas_diarias;
        CREATE TABLE contadores_senhas_diarias (
            data_atendimento TEXT NOT NULL,         -- Data no formato 'YYYY-MM-DD'
            categoria TEXT NOT NULL,                -- Ex: 'EXAME', 'CONSULTA', etc.
            ultimo_numero_senha INTEGER NOT NULL,
            PRIMARY KEY (data_atendimento, categoria)
        );

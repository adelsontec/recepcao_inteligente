# CuidarBot - Recepção Inteligente para Postos de Saúde

## 📝 Descrição do Projeto

O CuidarBot é um sistema de recepção inteligente projetado para otimizar e humanizar o atendimento inicial em postos de saúde. O sistema utiliza um chatbot conversacional para interagir com os pacientes, recolher informações de documentos através de OCR (Reconhecimento Ótico de Caracteres) e gerar senhas de atendimento sequenciais e categorizadas, que são reiniciadas diariamente.

O objetivo principal é reduzir o tempo de espera em filas físicas, especialmente em horários de grande movimento ou de madrugada, e fornecer à equipa do posto de saúde uma lista organizada dos pacientes que aguardam atendimento com os seus dados já parcialmente validados.

## ✨ Funcionalidades Principais

* **Chatbot Amigável:** Um assistente virtual (CuidarBot) que guia o utilizador através do processo.
* **Seleção de Categoria de Atendimento:** O utilizador pode escolher o tipo de serviço (Exame, Consulta, Dentista, Consulta Marcada).
* **Captura de Documento:** O utilizador envia uma foto de um documento de identificação (CNH, RG).
* **OCR (Reconhecimento Ótico de Caracteres):** Extração automática de dados como Nome, CPF e RG a partir da imagem do documento.
* **Validação de Dados:** O bot apresenta os dados extraídos para confirmação do utilizador.
* **Geração de Senha Sequencial e Categorizada:**
    * As senhas são geradas no formato `[PREFIXO_CATEGORIA]-[NÚMERO_SEQUENCIAL]` (ex: E-001, C-001).
    * A contagem de senhas é reiniciada para 1 todos os dias para cada categoria.
* **Restrição de Uma Senha por Pessoa por Dia:** O sistema verifica (usando o CPF) se o utilizador já retirou uma senha para qualquer categoria no dia atual.
* **Armazenamento de Dados:** As informações dos visitantes e as senhas geradas são guardadas numa base de dados SQLite.
* **Interface Web:** Construída com Flask para a interação do chat.
* **Página Administrativa (Visualização):** Uma página simples para visualizar as filas de atendimento do dia atual, organizadas por categoria.
* **Reinício Automático do Chat (Quiosque):** Após a exibição da senha, a interface do chat reinicia automaticamente após um período para o próximo utilizador.

## 🚀 Tecnologias Utilizadas

* **Linguagem de Programação:** Python
* **Framework Web:** Flask
* **OCR:** Tesseract OCR com a biblioteca `pytesseract`
* **Processamento de Imagem:** OpenCV (`opencv-python`), Pillow
* **Inteligência Artificial Conversacional:** API do Google Gemini (`google-generativeai`)
* **Banco de Dados:** SQLite
* **Frontend:** HTML, CSS, JavaScript (para a interface do chat)
* **Gestão de Ambiente:** `venv` (Ambiente Virtual Python)
* **Controlo de Versão:** Git e GitHub

## ⚙️ Como Executar o Projeto Localmente

1.  **Pré-requisitos:**
    * Python 3.x instalado
    * `pip` (gestor de pacotes Python)
    * `git` (para clonar o repositório)
    * Tesseract OCR instalado no sistema e o pacote de língua portuguesa (`tesseract-ocr-por`). No Debian/Ubuntu:
        ```bash
        sudo apt update
        sudo apt install tesseract-ocr tesseract-ocr-por
        ```
    * Bibliotecas de desenvolvimento para OpenCV (veja o guia de instalação anterior).

2.  **Clone o Repositório:**
    ```bash
    git clone [https://github.com/adelsontec/recepcao_inteligente.git](https://github.com/adelsontec/recepcao_inteligente.git)
    cd recepcao_inteligente
    ```

3.  **Crie e Ative o Ambiente Virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure as Variáveis de Ambiente:**
    * Crie um arquivo chamado `.env` na raiz do projeto.
    * Adicione o seguinte conteúdo, substituindo `SUA_CHAVE_API_GEMINI_AQUI` pela sua chave real:
        ```
        GOOGLE_API_KEY="SUA_CHAVE_API_GEMINI_AQUI"
        FLASK_APP=run.py
        FLASK_DEBUG=True
        # SECRET_KEY=uma_chave_secreta_muito_forte_para_sessoes (opcional, mas recomendado para sessões Flask)
        ```

6.  **Inicialize o Banco de Dados:**
    * Certifique-se de que o arquivo `app/schema.sql` existe com a estrutura correta das tabelas (`visitantes` e `contadores_senhas_diarias`).
    * Execute (a partir da raiz do projeto):
        ```bash
        python
        >>> from app import db_utils
        >>> db_utils.init_db()
        >>> exit()
        ```

7.  **Execute a Aplicação Flask:**
    ```bash
    flask run
    ```
    A aplicação estará disponível em `http://127.0.0.1:5000/`. A página de administração (se implementada) estará em `http://127.0.0.1:5000/admin_filas`.

## 🔮 Possíveis Melhorias Futuras

* **Melhorar a Precisão do OCR:** Experimentar mais técnicas de pré-processamento de imagem ou considerar APIs de OCR mais avançadas (como Google Cloud Vision API) para documentos difíceis.
* **Suporte a Mais Tipos de Documentos:** Adicionar lógica específica para Cartão do SUS ou outros documentos relevantes.
* **Captura de Imagem pela Câmera:** Implementar a funcionalidade para o utilizador tirar uma foto do documento diretamente pela interface, em vez de fazer upload.
* **Interface de Administração Mais Completa:** Adicionar funcionalidades para gerir filas (chamar próximo, remarcar, cancelar), editar dados de visitantes, visualizar estatísticas.
* **Notificações:** Integrar com sistemas de notificação (ex: SMS, painel de chamadas) para quando a senha do utilizador for chamada.
* **Segurança Avançada:** Implementar autenticação para a página de administração, proteção mais robusta contra ataques web.
* **Internacionalização (i18n):** Se necessário, adaptar para outros idiomas.
* **Testes Automatizados:** Criar testes unitários e de integração.

## 👨‍💻 Autor

* **Adelson Guimarães** - [adelsontec](https://github.com/adelsontec)

## 🙏 Agradecimentos (Opcional)

* Agradecimentos a [Nome da Instituição/Evento] pela oportunidade de desenvolver este projeto.
* Agradecimentos a [Nome de Mentores/Colegas] pela ajuda e feedback.

---

*Este README foi gerado para o projeto CuidarBot em [Maio de 2025].*

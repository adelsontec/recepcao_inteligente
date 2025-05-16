# CuidarBot - Recepção Inteligente para Postos de Saúde

## 📝 Descrição do Projeto

O CuidarBot é um sistema de recepção inteligente projetado para otimizar e humanizar o atendimento inicial em postos de saúde. O sistema utiliza um chatbot conversacional para interagir com os pacientes, recolher informações de documentos através de OCR (Reconhecimento Ótico de Caracteres) e gerar senhas de atendimento sequenciais e categorizadas, que são reiniciadas diariamente.

O objetivo principal é reduzir o tempo de espera em filas físicas, especialmente em horários de grande movimento ou de madrugada, e fornecer à equipa do posto de saúde uma lista organizada dos pacientes que aguardam atendimento com os seus dados já parcialmente validados.

## ✨ Funcionalidades Principais Atuais

* **Chatbot Amigável:** Um assistente virtual (CuidarBot) que guia o utilizador através do processo.
* **Seleção de Categoria de Atendimento:** O utilizador pode escolher o tipo de serviço (Exame, Consulta, Dentista, Consulta Marcada).
* **Captura de Documento:** O utilizador envia uma foto de um documento de identificação (CNH, RG).
* **OCR (Reconhecimento Ótico de Caracteres):** Extração automática de dados como Nome, CPF, RG e Data de Nascimento a partir da imagem do documento.
* **Cálculo de Idade:** A idade do paciente é calculada a partir da data de nascimento extraída.
* **Validação de Dados:** O bot apresenta os dados extraídos para confirmação do utilizador.
* **Geração de Senha Sequencial e Categorizada:**
    * As senhas são geradas no formato `[PREFIXO_CATEGORIA]-[NÚMERO_SEQUENCIAL]` (ex: E-001, C-001).
    * A contagem de senhas é reiniciada para 1 todos os dias para cada categoria.
* **Restrição de Uma Senha por Pessoa por Dia:** O sistema verifica (usando o CPF) se o utilizador já retirou uma senha para qualquer categoria no dia atual.
* **Armazenamento de Dados:** As informações dos visitantes (incluindo nome, cpf, rg, cns, data de nascimento, idade, categoria, senha e horário) são guardadas numa base de dados SQLite.
* **Interface Web:** Construída com Flask para a interação do chat.
* **Página Administrativa (Visualização):** Uma página para visualizar as filas de atendimento do dia atual (com nome, cpf, rg, data de nascimento, idade, senha, horário) e um dashboard simples com o total de atendimentos e contagem por categoria.
* **Reinício Automático do Chat (Quiosque):** Após a exibição da senha, a interface do chat reinicia automaticamente após um período para o próximo utilizador.

## 🚀 Tecnologias Utilizadas

* **Linguagem de Programação:** Python
* **Framework Web:** Flask
* **OCR:** Tesseract OCR com a biblioteca `pytesseract`
* **Processamento de Imagem:** OpenCV (`opencv-python`), Pillow
* **Inteligência Artificial Conversacional:** API do Google Gemini (`google-generativeai`)
* **Banco de Dados:** SQLite
* **Frontend:** HTML, CSS (Tailwind CSS), JavaScript (para a interface do chat e admin)
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
        sudo apt install tesseract-ocr tesseract-ocr-por opencv-python
        ```
    * Bibliotecas de desenvolvimento para OpenCV (geralmente instaladas com `opencv-python` ou através de `sudo apt install libopencv-dev python3-opencv`).

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
    A aplicação estará disponível em `http://127.0.0.1:5000/`. A página de administração estará em `http://127.0.0.1:5000/admin_filas`.

## 🔮 Possíveis Melhorias Futuras

### 🧠 Inteligência Artificial e Eficiência
* **Classificação automática de urgência (triagem):**
    * Treinar um modelo simples de IA para, com base nos dados inseridos ou sintomas descritos brevemente pelo paciente ao CuidarBot (após a geração da senha, como um passo opcional), sugerir uma prioridade de atendimento.
    * Isso ajudaria a organizar a fila com mais justiça, mesmo antes da chegada da equipe de saúde, alertando para casos potencialmente mais urgentes.
* **Aprimorar o OCR com IA moderna:**
    * Substituir ou complementar o `pytesseract` com APIs de OCR mais robustas como Google Cloud Vision API, ou explorar modelos como EasyOCR, Keras-OCR ou do Hugging Face.
    * Melhorar a leitura em documentos amassados, com ângulos variados, baixa iluminação ou fundos complexos.
* **Captura de Imagem pela Câmera:** Implementar a funcionalidade para o utilizador tirar uma foto do documento diretamente pela interface web, utilizando a câmera do dispositivo (PC ou telemóvel).

### 🧑‍⚕️ Experiência do Utilizador
* **Interface web com design responsivo e acessível (melhorias):**
    * Aprimorar a interface para celulares, tornando-a ainda mais fluida.
    * Considerar funcionalidades como QR code para retirada de senha (complementar ao bot).
    * Adicionar suporte para modo noturno.
    * Melhorar a acessibilidade com recursos de áudio para deficientes visuais (leitura de mensagens do bot).
* **Atendimento multicanal:**
    * Integrar o CuidarBot com plataformas como WhatsApp Business API ou Telegram para permitir que os pacientes iniciem o processo de atendimento remotamente.
    * Adaptar o sistema para totens físicos com tela touch para retirada de senhas no local.

### 🔐 Segurança e Privacidade
* **Autenticação e Criptografia de Dados (Avançado):**
    * Criptografar os dados pessoais sensíveis (como CPF, RG) no banco de dados (ex: usando `cryptography` em Python).
    * Adicionar autenticação (login e senha) para o acesso à página `/admin_filas`.
    * Considerar autenticação baseada em token JWT para futuras APIs.
* **Gestão de Consentimento (LGPD):** Adicionar um passo explícito de consentimento do utilizador para a recolha e processamento dos seus dados.

### 📊 Administração e Relatórios
* **Dashboard para os Gestores do Posto (Avançado):**
    * Expandir a página `/admin_filas` para incluir:
        * Gráficos de número de atendimentos por categoria ao longo do tempo.
        * Cálculo e exibição do tempo médio de espera (exigiria registar hora de chamada/finalização do atendimento).
        * Identificação de picos de atendimento.
        * Funcionalidade para exportação de relatórios das filas para formatos como CSV ou PDF.
* **Histórico e Análise Preditiva:**
    * Armazenar histórico de atendimentos de forma mais estruturada para permitir análises futuras.
    * Explorar modelos preditivos simples para ajudar o posto a planear escalas e recursos com base no histórico de procura.

### 🔌 Integrações e Expansão
* **Integração com sistemas do SUS ou e-SUS PEC:**
    * A longo prazo, investigar a possibilidade de integrar os dados de recepção ao prontuário eletrónico já utilizado pelo posto, através de APIs seguras (se disponíveis).
* **API RESTful para Integrar com Apps Externos:**
    * Expor endpoints seguros para que aplicativos municipais, painéis de chamada externos ou tablets da equipa de saúde possam buscar informações da fila em tempo real.

### 💡 Outras Ideias Criativas
* **Reconhecimento Facial para Check-in (Experimental e com Foco na Privacidade):**
    * Para pacientes frequentes, explorar o uso de reconhecimento facial (processado localmente no dispositivo do totem, sem enviar imagens para a nuvem, para manter a privacidade) como uma alternativa rápida ao OCR para check-in.
* **Sistema de Voz:**
    * Acrescentar reconhecimento de voz e síntese de fala para permitir que pacientes analfabetos, com dificuldade motora ou deficiência visual utilizem o sistema com comandos simples como "quero uma senha para consulta" ou "qual é a minha senha?".

## 👨‍💻 Autor

* **Adelson Guimarães** - [adelsontec](https://github.com/adelsontec)

## 🙏 Agradecimentos

* Agradecimentos à Imersão IA da Alura + Google pela oportunidade e aprendizado.
* *Adicione outros agradecimentos se desejar.*

---

*Este README foi gerado para o projeto CuidarBot em 16 de Maio de 2025.*

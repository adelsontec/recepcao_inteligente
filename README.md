# CuidarBot - Recepção Inteligente para Postos de Saúde

## 📝 Descrição do Projeto

O **CuidarBot** é um sistema de recepção inteligente projetado para otimizar e humanizar o atendimento inicial em postos de saúde. Utiliza um chatbot conversacional para interagir com os pacientes, recolher informações de documentos por OCR (Reconhecimento Ótico de Caracteres) e gerar senhas de atendimento sequenciais e categorizadas, reiniciadas diariamente.

O objetivo principal é reduzir o tempo de espera em filas físicas, especialmente em horários de grande movimento ou durante a madrugada, e fornecer à equipe do posto de saúde uma lista organizada dos pacientes com seus dados já parcialmente validados.

## ✨ Funcionalidades Principais Atuais

* **Chatbot Amigável**: guia o usuário durante todo o processo.
* **Seleção de Categoria de Atendimento**: Exame, Consulta, Dentista ou Consulta Marcada.
* **Captura de Documento**: envio de foto do documento (RG ou CNH).
* **OCR com `pytesseract`**: extrai nome, CPF, RG e data de nascimento.
* **Cálculo de Idade** a partir da data de nascimento extraída.
* **Validação de Dados** com confirmação pelo usuário.
* **Geração de Senha Sequencial e Categorizada** (ex: E-001, C-001), com reinício diário.
* **Restrição de Uma Senha por Pessoa por Dia** (via CPF).
* **Armazenamento em Banco SQLite**.
* **Interface Web (Flask)** para interação do chat.
* **Página Administrativa `/admin_filas`** com visão geral das filas do dia e contagem por categoria.
* **Reinício Automático do Chat (Modo Quiosque)** após a exibição da senha.

## 🚀 Tecnologias Utilizadas

* Python (com `venv`)
* Flask
* Tesseract OCR (`pytesseract`)
* OpenCV e Pillow
* API Google Gemini (conversação)
* SQLite
* Tailwind CSS + JS
* Git e GitHub

## ⚙️ Como Executar o Projeto Localmente

1. **Pré-requisitos:**
    ```bash
    sudo apt update
    sudo apt install tesseract-ocr tesseract-ocr-por libopencv-dev python3-opencv
    ```

2. **Clone o Repositório:**
    ```bash
    git clone https://github.com/adelsontec/recepcao_inteligente.git
    cd recepcao_inteligente
    ```

3. **Crie o Ambiente Virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

4. **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

5. **Configure o `.env`:**
    ```
    GOOGLE_API_KEY="SUA_CHAVE_API_GEMINI_AQUI"
    FLASK_APP=run.py
    FLASK_DEBUG=True
    ```

6. **Inicialize o Banco de Dados:**
    ```bash
    python
    >>> from app import db_utils
    >>> db_utils.init_db()
    >>> exit()
    ```

7. **Execute o Sistema:**
    ```bash
    flask run
    ```
    Acesse em: `http://127.0.0.1:5000/`  
    Admin: `http://127.0.0.1:5000/admin_filas`

## 🔮 Possíveis Melhorias Futuras

### 🧠 Inteligência Artificial
* Triagem por prioridade com IA
* OCR mais robusto com EasyOCR, Keras-OCR ou APIs modernas
* Captura de imagem pela câmera do dispositivo

### 🧑‍⚕️ Experiência do Usuário
* Design mais responsivo e acessível
* Suporte a QR Code, modo noturno e leitores de tela
* Integração com WhatsApp, Telegram e totens físicos

### 🔐 Segurança e LGPD
* Criptografia dos dados sensíveis (CPF, RG etc.)
* Autenticação para `/admin_filas` (login ou token)
* Consentimento explícito para uso de dados

### 📊 Gestão e Relatórios
* Dashboards com gráficos de atendimentos
* Tempo médio de espera e relatórios CSV/PDF
* Histórico de uso e análises preditivas

### 🔌 Integrações
* Integração com e-SUS PEC
* API RESTful para apps externos

### 💡 Ideias Criativas
* Reconhecimento facial (processamento local e seguro)
* Comandos por voz para acessibilidade

## 👨‍💻 Autor

**Adelson Guimarães** — [GitHub/adelsontec](https://github.com/adelsontec)

## 🙏 Agradecimentos

* Primeiramente, **agradeço a DEUS**, fonte de sabedoria, inspiração e propósito em tudo que construo.  
* À minha **esposa**, que com sensibilidade e amor, compartilhou a ideia original que deu origem a este projeto.  
* À **Imersão IA da Alura + Google**, pela oportunidade de aprendizado e desenvolvimento de soluções com impacto real.  
* À minha família, que me motiva todos os dias a usar a tecnologia para **cuidar de pessoas e transformar realidades com compaixão**.  
* A todos que acreditam que **a tecnologia pode ser uma ferramenta de serviço ao próximo, inclusão e dignidade**.

---

*Este README foi gerado para o projeto CuidarBot em 16 de Maio de 2025.*
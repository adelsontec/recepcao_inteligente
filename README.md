# CuidarBot - Recepção Inteligente para Postos de Saúde

## 📝 Descrição do Projeto

O CuidarBot é um sistema de recepção inteligente desenvolvido durante a Imersão IA Alura+Google, projetado para otimizar e humanizar o atendimento inicial em postos de saúde. O sistema utiliza um chatbot conversacional com a IA Google Gemini para interagir com os pacientes, recolher informações de documentos (foco em CNH para Nome, CPF e Data de Nascimento) através de OCR e gerar senhas de atendimento sequenciais e categorizadas.

O objetivo principal é reduzir o tempo de espera em filas físicas e fornecer à equipa do posto de saúde uma lista organizada dos pacientes com seus dados já parcialmente validados. O projeto também explora, como uma **visão de futuro e próxima atualização**, a integração de uma acompanhante virtual chamada **Lume** (desenvolvida com Google ADK) para oferecer suporte e entretenimento aos pacientes durante a espera.

## ✨ Funcionalidades Principais Atuais (CuidarBot)

* **Chatbot Amigável:** Guiado pela IA Google Gemini para uma interação natural.
* **Seleção de Categoria de Atendimento:** Exame, Consulta, Dentista ou Consulta Marcada.
* **Captura de Documento:** Envio de foto da CNH.
* **OCR com Pytesseract e OpenCV:** Extração automática de Nome, CPF e Data de Nascimento da CNH.
* **Cálculo de Idade:** Realizado a partir da data de nascimento extraída.
* **Fluxo de Input Manual:** Se o OCR não conseguir extrair os dados essenciais, o bot guia o utilizador para inseri-los manualmente.
* **Validação de Dados:** Confirmação dos dados (do OCR ou manuais) pelo próprio utilizador.
* **Geração de Senha Sequencial e Categorizada:** Ex: E-001, com reinício diário por categoria.
* **Restrição de Uma Senha por Pessoa por Dia:** Controle via CPF.
* **Armazenamento de Dados:** SQLite para informações dos visitantes e contadores de senha.
* **Interface Web Interativa:** Desenvolvida com Flask.
* **Página Administrativa (`/admin_filas`):**
    * Visualização das filas do dia por categoria (Nome, CPF, Data de Nascimento, Idade, Senha, Horário).
    * Dashboard simples com total de atendimentos e contagem por categoria.
    * Funcionalidade para apagar registos de visitantes (protegida por autenticação básica).
* **Modo Quiosque:** Reinício automático do chat do CuidarBot após 10 segundos da exibição da senha, com opção de QR Code para a Lume.

## 🚀 Tecnologias Utilizadas (CuidarBot)

* **Linguagem Principal:** Python 3.9+
* **Inteligência Artificial:** API Google Gemini
* **OCR:** Tesseract OCR, Pytesseract, OpenCV, Pillow
* **Framework Web:** Flask
* **Banco de Dados:** SQLite
* **Frontend:** HTML, Tailwind CSS, JavaScript (com biblioteca `qrcode.min.js` para exibir QR Code para a Lume)
* **Controlo de Versão:** Git e GitHub

## ⚙️ Como Executar o Projeto CuidarBot Localmente

(Mantenha as instruções de execução do CuidarBot como estavam no seu README anterior, garantindo que mencionam a necessidade do `.env` com `GOOGLE_API_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` e a inicialização do banco).
* **Exemplo para `.env`:**
  ```env
  GOOGLE_API_KEY="SUA_CHAVE_API_GEMINI_AQUI"
  FLASK_APP=run.py
  FLASK_DEBUG=True
  SECRET_KEY="SUA_CHAVE_SECRETA_FORTE_AQUI"
  ADMIN_USERNAME="seu_admin_user"
  ADMIN_PASSWORD="sua_admin_senha"
  LUME_PORT=5001 
  # LUME_URL_EXTERNA=http://seu_link_[cloudflare.com/lume/](https://cloudflare.com/lume/) (se estiver usando Cloudflare para Lume)

🔮 Possíveis Melhorias Futuras (Incluindo a Lume)
✨ Lume - Acompanhante de Fila com Google ADK (Protótipo Desenvolvido)
Conceito: Após o CuidarBot gerar a senha, um QR Code é exibido, direcionando o paciente para um chat com a Lume no seu próprio telemóvel (protótipo da Lume roda separadamente, por exemplo, na porta 5001).

Lume (Agente ADK): Uma assistente virtual desenvolvida com o Google Agent Development Kit (ADK) e modelos Gemini, projetada para:

Iniciar uma conversa acolhedora (perguntando nome, como a pessoa se sente).

Oferecer diferentes tipos de interação para tornar a espera mais agradável, através de agentes especialistas:

Agente de Relaxamento: Guiar exercícios de respiração e dar dicas de relaxamento.

Agente Espiritual/Motivacional: Partilhar mensagens de fé, versículos ou palavras de ânimo.

Agente de Curiosidades Leves: Contar fatos interessantes e divertidos.

Agente de Dicas para Mães/Pais: Oferecer sugestões para entreter ou acalmar crianças na fila.

Agente de Bem-estar/Saúde Simples: Dar lembretes como beber água ou fazer alongamentos leves.

Agente de Sugestões de Áudio/Podcast: Indicar tipos de podcasts ou músicas para passar o tempo.

Agente de Atividades Mentais: Propor pequenos jogos ou enigmas.

A Lume (no protótipo) utiliza um sistema de roteamento simples baseado em palavras-chave para acionar o agente especialista mais adequado.

Tecnologia do Protótipo Lume: Python, Google ADK, API Gemini, Flask (para uma interface web separada).

Estado Atual: Um protótipo funcional da Lume e seus agentes especialistas foi desenvolvido e testado, demonstrando a viabilidade do conceito. O código para este protótipo está na pasta lume_acompanhante_adk/ dentro deste repositório.

🧠 Inteligência Artificial e Eficiência (CuidarBot e Lume)
Triagem Otimizada no CuidarBot: Implementar uma triagem mais inteligente baseada em sintomas básicos.

OCR Avançado no CuidarBot: Explorar APIs como Google Cloud Vision para maior precisão.

Melhorar Roteamento da Lume: Usar análise de sentimento mais avançada ou a própria Lume para decidir qual especialista chamar.

🧑‍⚕️ Experiência do Utilizador
Integração QR Code Lume: Tornar a URL do QR Code mais dinâmica (ex: usando o IP da rede automaticamente) e hospedar a Lume de forma robusta para acesso público.

Acessibilidade: Melhorar acessibilidade do CuidarBot e da Lume.

Múltiplos Canais: Expandir CuidarBot e Lume para WhatsApp, Telegram.

🔐 Segurança e Privacidade
Autenticação Avançada: Para o painel admin do CuidarBot.

Criptografia de Dados: No CuidarBot.

📊 Administração e Relatórios (CuidarBot)
Dashboard Avançado: Com gráficos, tempo médio de espera, etc.

🔌 Integrações e Expansão
Integração com e-SUS PEC.

API Externa para CuidarBot.

👨‍💻 Autor
Adelson Guimarães — adelsontec

🙏 Agradecimentos
Primeiramente, agradeço a DEUS, fonte de sabedoria, inspiração e propósito em tudo que construo.

À minha esposa, que com sensibilidade e amor, compartilhou a ideia original que deu origem a este projeto.

À minha família, que me motiva todos os dias a usar a tecnologia para cuidar de pessoas e transformar realidades com compaixão.

À Imersão IA da Alura + Google, pela oportunidade de

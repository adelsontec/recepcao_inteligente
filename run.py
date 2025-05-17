# Versão final do projeto CuidarBot para Imersão IA Alura+Google
# run.py
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Em produção, você usaria um servidor WSGI como Gunicorn ou Waitress
    # Para desenvolvimento, o servidor do Flask é suficiente.
    # host='0.0.0.0' permite que a aplicação seja acessível na sua rede local
    # debug=True é pego da variável de ambiente FLASK_DEBUG (definida no .env)
    app.run(host='0.0.0.0', port=5000)

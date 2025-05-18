# lume_acompanhante_adk/run_lume_web.py
from app_lume import create_lume_app # Importa da subpasta app_lume
from dotenv import load_dotenv
import os

# Garante que lê o .env da pasta atual (lume_acompanhante_adk)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

app = create_lume_app()

if __name__ == "__main__":
    port = int(os.getenv("LUME_PORT", 5001)) # Porta diferente para Lume
    print(f"--- APLICATIVO WEB LUME: Iniciando servidor na porta {port} ---")
    app.run(host='0.0.0.0', port=port, debug=True)

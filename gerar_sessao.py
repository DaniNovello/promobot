from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()

api_id = os.environ.get("TELEGRAM_API_ID")
api_hash = os.environ.get("TELEGRAM_API_HASH")

print("--- INICIANDO LOGIN COM IDENTIDADE FIXA ---")

# Configuração fixa de dispositivo para evitar bloqueio de IP
client = TelegramClient(
    StringSession(), 
    api_id, 
    api_hash,
    device_model="PromoBot Server",
    system_version="Linux Cloud",
    app_version="1.0.0"
)

with client:
    print("\n✅ LOGIN COM SUCESSO!")
    print("\n=== COPIE O CÓDIGO ABAIXO E COLE NO RENDER ===\n")
    print(client.session.save())
    print("\n========================================================")
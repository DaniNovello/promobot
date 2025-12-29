import os
import asyncio
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Importando nossos módulos
import database
import ai_agent
import affiliate
import twitter_client

load_dotenv()

# --- CONFIGURAÇÃO FLASK (Healthcheck) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Afiliados está rodando! 🚀"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    # Pega a porta do ambiente (obrigatório para Render) ou usa 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO TELEGRAM ---
api_id = os.environ.get("TELEGRAM_API_ID")
api_hash = os.environ.get("TELEGRAM_API_HASH")
session_string = os.environ.get("TELEGRAM_SESSION")
channels_str = os.environ.get("CHANNELS_TO_MONITOR", "")

# --- A LINHA QUE FALTAVA ESTÁ AQUI ABAIXO ---
# Converte string de canais para lista de inteiros (se forem IDs) ou usernames
channels = [int(x.strip()) if x.strip().lstrip('-').isdigit() else x.strip() for x in channels_str.split(',') if x.strip()]

# Inicializa o Cliente
if session_string:
    # Modo Produção (Render)
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
else:
    # Modo Local (cria arquivo se não tiver string)
    client = TelegramClient('bot_session', api_id, api_hash)

@client.on(events.NewMessage(chats=channels))
async def handler(event):
    texto_original = event.message.message
    print(f"\n📩 Nova mensagem recebida do canal: {event.chat_id}")

    # 1. Extrair Link
    url_original = affiliate.extrair_link(texto_original)
    if not url_original:
        print("Ignorado: Nenhum link encontrado.")
        return

    # 2. Identificar Plataforma
    plataforma = affiliate.detectar_plataforma(url_original)
    if not plataforma:
        print(f"Ignorado: Plataforma não suportada ({url_original})")
        return

    # 3. Verificar Duplicidade no Supabase
    if database.verificar_duplicidade(url_original):
        print("Ignorado: Oferta já postada anteriormente.")
        return

    print(f"⚙️ Processando oferta da {plataforma}...")

    # 4. Converter Link (Afiliado)
    link_afiliado = affiliate.converter_link(url_original, plataforma)

    # 5. Gerar Copy com IA (Gemini)
    # Passamos o texto original para ele entender o contexto do produto
    copy_twitter = ai_agent.gerar_tweet(texto_original)

    # 6. Postar no Twitter
    sucesso = twitter_client.postar_no_x(copy_twitter, link_afiliado)

    # 7. Salvar no Banco de Dados
    if sucesso:
        database.salvar_oferta(url_original, link_afiliado, plataforma, copy_twitter)

async def main():
    print("🤖 Iniciando Bot de Afiliados...")
    await client.start()
    print("✅ Cliente Telegram conectado! Monitorando canais...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    # Inicia o servidor Flask em uma thread separada
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Inicia o loop do Telethon
    asyncio.run(main())
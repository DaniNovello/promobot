import os
import asyncio
import threading
import sys
import logging  # <--- ADICIONADO: Para ver erros de rede
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Importando nossos módulos
import database
import ai_agent
import affiliate
import twitter_client

# Força o carregamento do .env
load_dotenv()

# --- ATIVANDO LOGS DETALHADOS (CRUCIAL PARA O RENDER) ---
# Isso vai mostrar se o Telegram está recusando a conexão
logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO
)

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
    print(f"🌍 Iniciando servidor Flask na porta {port}...")
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- INÍCIO DO DIAGNÓSTICO ---
print("\n" + "="*40)
print("🔎 INICIANDO DIAGNÓSTICO DE AMBIENTE")
print("="*40)

api_id = os.environ.get("TELEGRAM_API_ID")
api_hash = os.environ.get("TELEGRAM_API_HASH")
session_string = os.environ.get("TELEGRAM_SESSION")
channels_str = os.environ.get("CHANNELS_TO_MONITOR", "")

# 1. Verifica API ID e HASH
if api_id and api_hash:
    print(f"✅ API_ID detectado: {api_id}")
    print("✅ API_HASH detectado: [OK]")
else:
    print("❌ ERRO: API_ID ou API_HASH estão faltando!")

# 2. Verifica a Session String
if session_string:
    print(f"✅ SESSION_STRING detectada! Comprimento: {len(session_string)} caracteres.")
    if len(session_string) < 50:
        print("⚠️ AVISO CRÍTICO: A Session String parece muito curta. Verifique se copiou inteira.")
else:
    print("❌ ERRO CRÍTICO: Variável TELEGRAM_SESSION está vazia ou não existe!")

# 3. Verifica Canais
print(f"📡 Canais configurados: {channels_str}")
try:
    channels = [int(x.strip()) if x.strip().lstrip('-').isdigit() else x.strip() for x in channels_str.split(',') if x.strip()]
    print(f"✅ Lista de canais processada: {channels}")
except Exception as e:
    print(f"❌ Erro ao processar lista de canais: {e}")
    channels = []

print("="*40 + "\n")

# --- INICIALIZAÇÃO DO CLIENTE (COM IDENTIDADE FIXA) ---
if session_string:
    try:
        print("🔌 Criando cliente com Identidade Fixa (PromoBot Server)...")
        client = TelegramClient(
            StringSession(session_string), 
            api_id, 
            api_hash,
            device_model="PromoBot Server",
            system_version="Linux Cloud",
            app_version="1.0.0"
        )
    except Exception as e:
        print(f"❌ FALHA AO CRIAR CLIENTE: {e}")
        # Fallback básico
        client = TelegramClient('bot_session', api_id, api_hash)
else:
    print("⚠️ Criando cliente SEM sessão (vai pedir login)...")
    client = TelegramClient('bot_session', api_id, api_hash)

@client.on(events.NewMessage(chats=channels))
async def handler(event):
    try:
        print(f"\n📩 Nova mensagem recebida do canal: {event.chat_id}")
        texto_original = event.message.message

        # 1. Extrair Link
        url_original = affiliate.extrair_link(texto_original)
        if not url_original:
            print("   ↳ Ignorado: Nenhum link encontrado.")
            return

        # 2. Identificar Plataforma
        plataforma = affiliate.detectar_plataforma(url_original)
        if not plataforma:
            print(f"   ↳ Ignorado: Plataforma não suportada ({url_original})")
            return

        # 3. Verificar Duplicidade
        if database.verificar_duplicidade(url_original):
            print("   ↳ Ignorado: Oferta duplicada.")
            return

        print(f"⚙️ Processando oferta da {plataforma}...")

        # 4. Converter Link
        link_afiliado = affiliate.converter_link(url_original, plataforma)

        # 5. Gerar Copy (IA)
        copy_twitter = ai_agent.gerar_tweet(texto_original)

        # 6. Postar
        sucesso = twitter_client.postar_no_x(copy_twitter, link_afiliado)

        # 7. Salvar
        if sucesso:
            database.salvar_oferta(url_original, link_afiliado, plataforma, copy_twitter)
            
    except Exception as e:
        print(f"❌ ERRO NO HANDLER: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("🤖 Função main iniciada.")
    try:
        print("⏳ Tentando conectar ao Telegram (Timeout de 30s)...")
        # ADICIONADO: Timeout para não travar eternamente se o IP estiver bloqueado
        await asyncio.wait_for(client.connect(), timeout=30)
        
        # Verifica se realmente logou
        if not await client.is_user_authorized():
            print("\n" + "!"*50)
            print("❌ ERRO CRÍTICO: SESSÃO NÃO AUTORIZADA")
            print("   O Telegram rejeitou a conexão. Motivo provável: Troca de IP ou Sessão Revogada.")
            print("   SOLUÇÃO: Gere uma nova chave usando o 'gerar_sessao.py' novo e atualize no Render.")
            print("!"*50 + "\n")
            return

        # SE CHEGAR AQUI, O LOGIN FUNCIONOU
        print("\n" + "*"*40)
        print("✅ ✅ SUCESSO! O BOT ESTÁ CONECTADO E RODANDO! ✅ ✅")
        print("*"*40 + "\n")
        
        print("👀 Monitorando mensagens...")
        await client.run_until_disconnected()

    except asyncio.TimeoutError:
        print("\n❌ ERRO DE CONEXÃO: O Render não conseguiu alcançar o Telegram em 30s.")
        print("   Isso indica BLOQUEIO DE IP. Tente reiniciar o serviço no Render para pegar outro IP.")
        
    except Exception as e:
        print("\n" + "!"*40)
        print(f"❌ ERRO FATAL NA CONEXÃO: {e}")
        print("!"*40 + "\n")

if __name__ == '__main__':
    # Inicia Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Inicia Loop do Bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot interrompido pelo usuário.")
    except Exception as e:
        print(f"❌ Erro não tratado: {e}")
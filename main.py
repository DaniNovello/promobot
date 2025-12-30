import os
import asyncio
import threading
import sys
import logging
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

# --- CONFIGURAÇÃO DE LOGS (CORRIGIDA PARA RENDER) ---
# 'force=True' e 'stream=sys.stdout' garantem que o log apareça no painel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger("MainBot")

# --- CONFIGURAÇÃO FLASK (Healthcheck) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Afiliados está rodando! 🚀"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🌍 Iniciando servidor Flask na porta {port}...")
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- CONFIGURAÇÕES ---
api_id = os.environ.get("TELEGRAM_API_ID")
api_hash = os.environ.get("TELEGRAM_API_HASH")
session_string = os.environ.get("TELEGRAM_SESSION")
channels_str = os.environ.get("CHANNELS_TO_MONITOR", "")

# Tratamento da lista de canais
try:
    channels = [int(x.strip()) if x.strip().lstrip('-').isdigit() else x.strip() for x in channels_str.split(',') if x.strip()]
    logger.info(f"📡 Canais configurados: {channels}")
except Exception as e:
    logger.error(f"❌ Erro ao processar lista de canais: {e}")
    channels = []

# --- INICIALIZAÇÃO DO CLIENTE (COM IDENTIDADE FIXA) ---
if session_string:
    try:
        logger.info("🔌 Criando cliente com Identidade Fixa (PromoBot Server)...")
        client = TelegramClient(
            StringSession(session_string), 
            api_id, 
            api_hash,
            device_model="PromoBot Server",
            system_version="Linux Cloud",
            app_version="1.0.0"
        )
    except Exception as e:
        logger.error(f"❌ FALHA AO CRIAR CLIENTE: {e}")
        client = TelegramClient('bot_session', api_id, api_hash)
else:
    logger.warning("⚠️ Criando cliente SEM sessão (vai pedir login)...")
    client = TelegramClient('bot_session', api_id, api_hash)

@client.on(events.NewMessage(chats=channels))
async def handler(event):
    logger.info(f"📩 Nova mensagem recebida do canal: {event.chat_id}")
    try:
        texto_original = event.message.message

        # 1. Extrair Link
        url_original = affiliate.extrair_link(texto_original)
        if not url_original:
            logger.info("   ↳ Ignorado: Nenhum link encontrado.")
            return

        # 2. Identificar Plataforma
        plataforma = affiliate.detectar_plataforma(url_original)
        if not plataforma:
            logger.info(f"   ↳ Ignorado: Plataforma não suportada ({url_original})")
            return

        # 3. Verificar Duplicidade
        if database.verificar_duplicidade(url_original):
            logger.info("   ↳ Ignorado: Oferta duplicada.")
            return

        logger.info(f"⚙️ Processando oferta da {plataforma}...")

        # 4. Converter Link
        link_afiliado = affiliate.converter_link(url_original, plataforma)

        # 5. Gerar Copy (IA)
        copy_twitter = ai_agent.gerar_tweet(texto_original)

        # 6. Postar
        logger.info(f"🐦 Tentando postar no Twitter: {link_afiliado}")
        sucesso = twitter_client.postar_no_x(copy_twitter, link_afiliado)

        # 7. Salvar
        if sucesso:
            logger.info("✅ Sucesso! Salvando no banco...")
            database.salvar_oferta(url_original, link_afiliado, plataforma, copy_twitter)
        else:
            logger.error("❌ Falha na postagem do Twitter (não salvo no banco).")
            
    except Exception as e:
        logger.error(f"❌ ERRO NO HANDLER: {e}", exc_info=True)

async def main():
    logger.info("🤖 Função main iniciada.")

    # --- NOVIDADE: TESTE DE CREDENCIAIS ---
    logger.info("🔑 Testando credenciais do Twitter antes de conectar...")
    if not twitter_client.testar_credenciais():
        logger.critical("⚠️ AS CREDENCIAIS DO TWITTER ESTÃO INVÁLIDAS OU SEM PERMISSÃO!")
        # Não damos return para você ver o log completo, mas o bot não vai postar.
    else:
        logger.info("✅ Credenciais do Twitter VÁLIDAS!")
    # --------------------------------------

    try:
        logger.info("⏳ Tentando conectar ao Telegram (Timeout de 30s)...")
        await asyncio.wait_for(client.connect(), timeout=30)
        
        # Verifica se realmente logou
        if not await client.is_user_authorized():
            logger.critical("\n" + "!"*50)
            logger.critical("❌ ERRO CRÍTICO: SESSÃO NÃO AUTORIZADA")
            logger.critical("   O Telegram rejeitou a conexão. Motivo provável: Troca de IP ou Sessão Revogada.")
            logger.critical("   SOLUÇÃO: Gere uma nova chave usando o 'gerar_sessao.py' novo e atualize no Render.")
            logger.critical("!"*50 + "\n")
            return

        # SE CHEGAR AQUI, O LOGIN FUNCIONOU
        logger.info("\n" + "*"*40)
        logger.info("✅ ✅ SUCESSO! O BOT ESTÁ CONECTADO E RODANDO! ✅ ✅")
        logger.info("*"*40 + "\n")
        
        logger.info("👀 Monitorando mensagens...")
        await client.run_until_disconnected()

    except asyncio.TimeoutError:
        logger.error("\n❌ ERRO DE CONEXÃO: O Render não conseguiu alcançar o Telegram em 30s.")
        logger.error("   Isso indica BLOQUEIO DE IP. Tente reiniciar o serviço no Render para pegar outro IP.")
        
    except Exception as e:
        logger.critical(f"❌ ERRO FATAL NA CONEXÃO: {e}", exc_info=True)

if __name__ == '__main__':
    # Inicia Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Inicia Loop do Bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário.")
    except Exception as e:
        logger.critical(f"❌ Erro não tratado: {e}")
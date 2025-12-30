import os
import tweepy
import logging
from dotenv import load_dotenv

load_dotenv()

# Configuração de Logs para o Twitter
logger = logging.getLogger("TwitterClient")

def get_twitter_client():
    return tweepy.Client(
        consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
        consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
    )

def testar_credenciais():
    """Testa se as chaves do Twitter estão válidas ao iniciar."""
    try:
        client = get_twitter_client()
        me = client.get_me()
        if me.data:
            logger.info(f"✅ Twitter Autenticado: @{me.data.username}")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO NO TWITTER: {e}")
        return False

def postar_no_x(texto, link):
    client = get_twitter_client()
    try:
        # Monta o tweet final
        tweet_final = f"{texto}\n\n🛒 Link: {link}"
        response = client.create_tweet(text=tweet_final)
        logger.info(f"🐦 Tweet postado com sucesso! ID: {response.data['id']}")
        return True
    except Exception as e:
        logger.error(f"❌ Falha ao postar no Twitter: {e}")
        return False
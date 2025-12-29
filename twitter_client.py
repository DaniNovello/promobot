import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

def get_twitter_client():
    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
        consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
    )
    return client

def postar_no_x(texto, link):
    client = get_twitter_client()
    try:
        # Monta o tweet final
        tweet_final = f"{texto}\n\n🛒 Link: {link}"
        response = client.create_tweet(text=tweet_final)
        print(f"🐦 Tweet postado com sucesso! ID: {response.data['id']}")
        return True
    except Exception as e:
        print(f"❌ Erro ao postar no Twitter: {e}")
        return False
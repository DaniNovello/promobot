import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def gerar_tweet(texto_original, preco=None):
    """Usa o Gemini para criar um tweet atrativo."""
    # CORREÇÃO: Atualizado para o modelo mais recente e rápido
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Atue como um especialista em marketing digital e copywriter para o Twitter (X).
    Sua tarefa é reescrever a seguinte oferta de produto para ser postada.
    
    Texto original: "{texto_original}"
    
    Regras:
    1. O texto deve ter no máximo 240 caracteres (para sobrar espaço para o link).
    2. Use 2 ou 3 emojis relevantes.
    3. Use gatilhos mentais de urgência ou oportunidade (ex: "Corre!", "Preço bugado!", "Imperdível").
    4. Adicione 2 hashtags populares relacionadas ao produto (ex: #promoção #oferta).
    5. NÃO coloque o link no texto, o link será adicionado depois.
    6. Seja informal e direto.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erro no Gemini: {e}")
        # Fallback simples caso a IA falhe
        return f"🔥 Oferta imperdível encontrada! Aproveite antes que acabe. 🚀 #promoção"
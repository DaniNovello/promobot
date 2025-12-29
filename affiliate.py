import os
import re
import requests
import json
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

def detectar_plataforma(url):
    domain = url.lower()
    if "amazon" in domain or "amzn" in domain:
        return "Amazon"
    elif "shopee" in domain or "shp.ee" in domain:
        return "Lomadee"
    elif "mercadolivre" in domain or "mercadolivre.com" in domain:
        return "Lomadee"
    elif "magazineluiza" in domain or "magalu" in domain:
        return "Lomadee"
    elif "nike" in domain or "centauro" in domain or "netshoes" in domain:
        return "Lomadee"
    return "Outros"

def expandir_url(url_curta):
    """
    Expande links encurtados (amzn.to, shp.ee, bit.ly) para pegar a URL real.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.head(url_curta, allow_redirects=True, timeout=10, headers=headers)
        return response.url
    except Exception as e:
        print(f"⚠️ Erro ao expandir URL: {e}")
        return url_curta

def gerar_link_lomadee_api(url_original):
    """
    Consulta a API v3 da Lomadee.
    """
    app_token = os.environ.get("LOMADEE_APP_TOKEN")
    source_id = os.environ.get("LOMADEE_SOURCE_ID")

    # --- TRAVA DE SEGURANÇA ---
    # Se o token não estiver configurado ou for o placeholder, retorna original
    if not app_token or "cole_seu" in app_token:
        print("⚠️ Lomadee: Token pendente. Postando link original (sem comissão) para manter engajamento.")
        return url_original
    # --------------------------

    # Endpoint oficial da API v3
    endpoint = f"https://api.lomadee.com/v3/{app_token}/deeplink/_create"
    
    params = {
        "sourceId": source_id,
        "url": url_original
    }

    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and "deeplinks" in data:
            if len(data["deeplinks"]) > 0:
                link_gerado = data["deeplinks"][0]["deeplink"]
                return link_gerado
        
        print(f"⚠️ Erro API Lomadee: {data}")
        return url_original

    except Exception as e:
        print(f"❌ Erro na requisição Lomadee: {e}")
        return url_original

def converter_link(url, plataforma_detectada):
    url_final = expandir_url(url)
    
    try:
        if plataforma_detectada == "Amazon":
            tag = os.environ.get("AMAZON_TAG")
            if not tag: return url_final
            
            parsed = urlparse(url_final)
            query = parse_qs(parsed.query)
            query.pop('tag', None)
            query.pop('ascsubtag', None)
            query['tag'] = [tag]
            
            new_query = urlencode(query, doseq=True)
            new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
            return new_url

        elif plataforma_detectada == "Lomadee":
            return gerar_link_lomadee_api(url_final)
            
        return url_final

    except Exception as e:
        print(f"❌ Erro geral na conversão: {e}")
        return url_final

def extrair_link(texto):
    url_regex = r'(https?://[^\s]+)'
    match = re.search(url_regex, texto)
    if match:
        return match.group(0)
    return None
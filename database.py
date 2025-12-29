import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def verificar_duplicidade(link_original):
    """Verifica se o link já foi postado nas últimas 24h (ou ever, dependendo da lógica)."""
    try:
        response = supabase.table('ofertas').select("*").eq('link_original', link_original).execute()
        # Se a lista de dados não estiver vazia, já existe
        if response.data and len(response.data) > 0:
            return True
        return False
    except Exception as e:
        print(f"Erro ao verificar duplicidade: {e}")
        return False # Na dúvida, deixa passar (ou bloqueia, dependendo da estratégia)

def salvar_oferta(link_original, link_afiliado, plataforma, texto_postado):
    """Salva o log da postagem."""
    data = {
        "link_original": link_original,
        "link_afiliado": link_afiliado,
        "plataforma": plataforma,
        "texto_postado": texto_postado
    }
    try:
        supabase.table('ofertas').insert(data).execute()
        print(f"✅ Oferta salva no banco: {plataforma}")
    except Exception as e:
        print(f"❌ Erro ao salvar no banco: {e}")
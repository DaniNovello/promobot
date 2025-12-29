import os
from dotenv import load_dotenv
import affiliate

load_dotenv()

print("--- TESTE DE API LOMADEE ---\n")

# Use um produto real da Shopee aqui para testar
link_shopee = "https://shopee.com.br/product/12345678/12345678" 

print(f"🔹 Enviando para API: {link_shopee}")
link_gerado = affiliate.converter_link(link_shopee, "Lomadee")

print(f"🔸 Resposta da API: {link_gerado}")

if "lomadee.com" in link_gerado or "socialsoul" in link_gerado:
    print("✅ SUCESSO! A API retornou um link válido.")
else:
    print("❌ AVISO: A API retornou o link original (verifique o Token).")
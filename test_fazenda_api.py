"""
Test script to query Fazenda MG API with a real RENAVAM
This will show us what data the API returns
"""
import requests
import json

# We'll need a valid CAPTCHA token
# For now, let's try to understand the API response structure

def test_api_call(renavam, token):
    """Test API call with RENAVAM and token"""
    url = f"https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/api/extrato-debito/renavam/{renavam}/"
    
    headers = {
        'Token': token,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Origin': 'https://buscar-renavam-ipva-digital.fazenda.mg.gov.br',
        'Referer': 'https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/'
    }
    
    try:
        print(f"🔍 Testando API com RENAVAM: {renavam}")
        print(f"📡 URL: {url}")
        print(f"🔑 Token: {token[:20]}..." if len(token) > 20 else f"🔑 Token: {token}")
        print()
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCESSO! Dados retornados:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        elif response.status_code == 401:
            print("❌ Token inválido ou expirado")
            print(f"Response: {response.text}")
        else:
            print(f"⚠️ Erro {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")
        
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DA API OFICIAL DA FAZENDA MG")
    print("=" * 60)
    print()
    
    # Para testar, precisamos de:
    # 1. Um RENAVAM válido de MG
    # 2. Um token de CAPTCHA válido
    
    print("⚠️ INSTRUÇÕES:")
    print("1. Acesse: https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/")
    print("2. Abra o DevTools (F12)")
    print("3. Resolva o CAPTCHA manualmente")
    print("4. Na aba Network, procure pela chamada à API")
    print("5. Copie o header 'Token' da requisição")
    print("6. Cole aqui quando solicitado")
    print()
    
    # Exemplo de RENAVAM (você precisa usar um válido)
    renavam = input("Digite um RENAVAM válido de MG: ").strip()
    token = input("Digite o Token do CAPTCHA: ").strip()
    
    if renavam and token:
        test_api_call(renavam, token)
    else:
        print("❌ RENAVAM ou Token não fornecido")

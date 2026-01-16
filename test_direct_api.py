#!/usr/bin/env python3
"""
Teste DIRETO da API Fazenda sem CAPTCHA
Vamos ver se a API é pública!
"""
import requests
import json

RENAVAM = "01293554640"
API_URL = f"https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/api/extrato-debito/renavam/{RENAVAM}/"

print("=" * 70)
print("TESTE: API FAZENDA MG DIRETA (SEM CAPTCHA)")
print("=" * 70)
print()
print(f"📋 RENAVAM: {RENAVAM}")
print(f"🌐 URL: {API_URL}")
print()

# Tentar chamada direta
print("🚀 Fazendo request direto...")
print()

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Origin': 'https://buscar-renavam-ipva-digital.fazenda.mg.gov.br',
    'Referer': 'https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/'
}

try:
    response = requests.get(API_URL, headers=headers, timeout=30)
    
    print(f"📊 Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        print("✅ SUCESSO! API É PÚBLICA!")
        print("=" * 70)
        
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        print("=" * 70)
        print()
        
        # Salvar resultado
        with open('/tmp/fazenda_direct_api.json', 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("💾 Resultado salvo em: /tmp/fazenda_direct_api.json")
        print()
        print("🎉 DESCOBERTA IMPORTANTE:")
        print("   A API da Fazenda MG é PÚBLICA e não requer CAPTCHA!")
        print("   Podemos fazer consultas diretas sem custo do 2Captcha!")
        
    elif response.status_code == 401:
        print("❌ 401 Unauthorized - Requer token/autenticação")
        print("   Precisamos do 2Captcha para obter token")
        
    elif response.status_code == 403:
        print("❌ 403 Forbidden - Bloqueado")
        print("   Pode ser Cloudflare ou outra proteção")
        
    elif response.status_code == 404:
        print("❌ 404 Not Found - RENAVAM inválido ou endpoint errado")
        
    else:
        print(f"⚠️  Status inesperado: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("❌ Timeout - API não respondeu")
    
except requests.exceptions.ConnectionError:
    print("❌ Erro de conexão")
    
except Exception as e:
    print(f"❌ Erro: {e}")

print()
print("=" * 70)

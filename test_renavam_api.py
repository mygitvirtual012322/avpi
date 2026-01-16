#!/usr/bin/env python3
"""
Teste direto da API Fazenda com 2Captcha usando RENAVAM
"""
import asyncio
import json
from fazenda_api_client import FazendaAPIClient

# RENAVAM de teste (do seu código anterior)
RENAVAM_TESTE = "01293554640"

async def test_renavam_query():
    print("=" * 70)
    print("TESTE: API FAZENDA MG COM 2CAPTCHA (RENAVAM)")
    print("=" * 70)
    print()
    
    print(f"📋 RENAVAM: {RENAVAM_TESTE}")
    print()
    
    # Criar cliente
    client = FazendaAPIClient()
    
    # Consultar API
    print("🚀 Iniciando consulta...")
    print()
    
    result = await client.get_vehicle_data_async(RENAVAM_TESTE)
    
    if result:
        print()
        print("=" * 70)
        print("✅ SUCESSO! DADOS RETORNADOS:")
        print("=" * 70)
        print()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()
        print("=" * 70)
        
        # Salvar resultado
        with open('/tmp/fazenda_api_result.json', 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("💾 Resultado salvo em: /tmp/fazenda_api_result.json")
        
        return result
    else:
        print()
        print("=" * 70)
        print("❌ FALHA - Não conseguiu obter dados")
        print("=" * 70)
        print()
        print("Possíveis causas:")
        print("- Saldo 2Captcha insuficiente")
        print("- RENAVAM inválido")
        print("- Problema com Turnstile")
        print("- API da Fazenda fora do ar")
        
        return None

if __name__ == "__main__":
    print()
    print("🎯 Este teste vai:")
    print("   1. Resolver o Turnstile CAPTCHA com 2Captcha")
    print("   2. Consultar a API oficial da Fazenda MG")
    print("   3. Retornar todos os dados do veículo")
    print()
    print("⏱️  Tempo estimado: 15-30 segundos")
    print()
    input("Pressione ENTER para começar...")
    print()
    
    result = asyncio.run(test_renavam_query())
    
    if result:
        print()
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print()
        print("📊 Próximos passos:")
        print("   - Verificar estrutura dos dados retornados")
        print("   - Integrar parsing no plate_calculator.py")
        print("   - Testar com diferentes RENAVAMs")
    else:
        print()
        print("⚠️  TESTE FALHOU - Verifique os logs acima")

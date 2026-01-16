#!/usr/bin/env python3
"""
Script simples para testar a configuração do 2Captcha
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_config():
    print("=" * 70)
    print("TESTE DE CONFIGURAÇÃO 2CAPTCHA")
    print("=" * 70)
    print()
    
    # Check API key
    api_key = os.getenv('CAPTCHA_API_KEY', '')
    
    if not api_key:
        print("❌ CAPTCHA_API_KEY não configurada!")
        print()
        print("Para configurar:")
        print("1. Copie .env.example para .env")
        print("2. Edite .env e adicione sua API key")
        print("3. Execute este script novamente")
        return False
    
    print(f"✅ API Key encontrada: {api_key[:10]}...{api_key[-4:]}")
    
    # Check 2captcha-python
    try:
        from twocaptcha import TwoCaptcha
        print("✅ Biblioteca 2captcha-python instalada")
        
        # Check balance
        try:
            solver = TwoCaptcha(api_key)
            balance = solver.balance()
            print(f"✅ Saldo 2Captcha: ${balance}")
            
            if float(balance) < 0.01:
                print("⚠️  Saldo baixo! Adicione créditos em: https://2captcha.com/pay")
            
        except Exception as e:
            print(f"⚠️  Erro ao verificar saldo: {e}")
            print("   Verifique se a API key está correta")
            
    except ImportError:
        print("❌ Biblioteca 2captcha-python não instalada")
        print("   Execute: pip install 2captcha-python")
        return False
    
    # Check playwright
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright instalado")
        
        # Check if browsers are installed
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("✅ Chromium instalado e funcionando")
        except Exception as e:
            print(f"⚠️  Chromium não instalado: {e}")
            print("   Execute: playwright install chromium")
            
    except ImportError:
        print("❌ Playwright não instalado")
        print("   Execute: pip install playwright && playwright install chromium")
        return False
    
    print()
    print("=" * 70)
    print("✅ CONFIGURAÇÃO OK! Pronto para usar 2Captcha")
    print("=" * 70)
    print()
    print("Próximos passos:")
    print("1. Testar integração: python test_2captcha_quick.py")
    print("2. Testar com placa: python -c \"from plate_calculator import calculate_ipva_data; print(calculate_ipva_data('ABC1234'))\"")
    print()
    
    return True

if __name__ == "__main__":
    test_config()

#!/usr/bin/env python3
"""
Quick test script for 2Captcha integration
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, '/Users/davidpraxedes/Downloads/ipva')

from fazenda_api_2captcha import test_2captcha_integration

API_KEY = os.getenv('CAPTCHA_API_KEY', '')
RENAVAM = "01293554640"

if __name__ == "__main__":
    print("🚀 Testando 2Captcha...")
    print()
    
    if not API_KEY:
        print("❌ CAPTCHA_API_KEY não configurada!")
        print("Configure no arquivo .env ou variável de ambiente")
        sys.exit(1)
    
    result = asyncio.run(test_2captcha_integration(RENAVAM, API_KEY))
    
    if result:
        print("\n✅ TESTE BEM-SUCEDIDO!")
    else:
        print("\n⚠️ Teste não completou - veja logs acima")

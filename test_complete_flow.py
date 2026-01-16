#!/usr/bin/env python3
"""
Teste COMPLETO: Fazenda API com 2Captcha
Fluxo: Digitar RENAVAM → Resolver Turnstile → Consultar API
"""
import asyncio
import json
import os
import requests
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

FAZENDA_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"
CAPTCHA_API_URL = "https://api.2captcha.com"
API_KEY = os.getenv('CAPTCHA_API_KEY', '')
SITEKEY = "0x4AAAAAAAWV7kjZLnydRbx6"  # Extraído anteriormente
RENAVAM = "01293554640"

async def test_complete_flow():
    print("=" * 70)
    print("TESTE COMPLETO: FAZENDA API + 2CAPTCHA")
    print("=" * 70)
    print()
    print(f"📋 RENAVAM: {RENAVAM}")
    print(f"🔑 Sitekey: {SITEKEY}")
    print()
    
    if not API_KEY:
        print("❌ CAPTCHA_API_KEY não configurada!")
        return None
    
    # Passo 1: Resolver Turnstile com 2Captcha
    print("🤖 Passo 1: Resolvendo Turnstile com 2Captcha...")
    print()
    
    task_payload = {
        "clientKey": API_KEY,
        "task": {
            "type": "TurnstileTaskProxyless",
            "websiteURL": FAZENDA_URL,
            "websiteKey": SITEKEY
        }
    }
    
    print("📤 Enviando task para 2Captcha...")
    create_response = requests.post(
        f"{CAPTCHA_API_URL}/createTask",
        json=task_payload,
        timeout=30
    )
    
    create_result = create_response.json()
    
    if create_result.get('errorId') != 0:
        print(f"❌ Erro ao criar task: {create_result.get('errorDescription')}")
        return None
    
    task_id = create_result['taskId']
    print(f"✅ Task criada: {task_id}")
    print(f"⏳ Aguardando resolução (10-30 segundos)...")
    print()
    
    # Poll for result
    max_attempts = 60
    attempt = 0
    turnstile_token = None
    
    while attempt < max_attempts:
        await asyncio.sleep(2)
        attempt += 1
        
        result_response = requests.post(
            f"{CAPTCHA_API_URL}/getTaskResult",
            json={
                "clientKey": API_KEY,
                "taskId": task_id
            },
            timeout=30
        )
        
        result = result_response.json()
        
        if result.get('status') == 'ready':
            turnstile_token = result['solution']['token']
            cost = result.get('cost', 'unknown')
            print(f"✅ Turnstile resolvido!")
            print(f"🎫 Token: {turnstile_token[:50]}...")
            print(f"💰 Custo: ${cost}")
            break
            
        elif result.get('status') == 'processing':
            if attempt % 5 == 0:
                print(f"   Aguardando... ({attempt}/{max_attempts})")
        else:
            print(f"❌ Erro: {result}")
            return None
    
    if not turnstile_token:
        print("❌ Timeout aguardando resolução")
        return None
    
    # Passo 2: Usar token para consultar API
    print()
    print("🚀 Passo 2: Consultando API da Fazenda com token...")
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Capturar resposta da API
        captured_response = None
        
        async def handle_response(response):
            nonlocal captured_response
            if '/api/extrato-debito/renavam/' in response.url and response.status == 200:
                try:
                    captured_response = await response.json()
                    print(f"✅ Resposta da API capturada!")
                except:
                    pass
        
        page.on('response', handle_response)
        
        # Navegar e preencher
        await page.goto(FAZENDA_URL)
        await asyncio.sleep(2)
        
        # Digitar RENAVAM
        input_field = await page.query_selector('input[type="text"]')
        if input_field:
            await input_field.fill(RENAVAM)
            print(f"✅ RENAVAM preenchido: {RENAVAM}")
            await asyncio.sleep(2)
            
            # Injetar token do Turnstile
            print(f"💉 Injetando token Turnstile...")
            await page.evaluate(f'''(token) => {{
                const input = document.querySelector('[name="cf-turnstile-response"]');
                if (input) {{
                    input.value = token;
                }}
                
                // Tentar chamar callback
                if (window.turnstileCallback) {{
                    window.turnstileCallback(token);
                }}
            }}''', turnstile_token)
            
            await asyncio.sleep(1)
            
            # Clicar em consultar
            print(f"🖱️  Clicando em consultar...")
            button = await page.query_selector('button[type="submit"]') or \
                    await page.query_selector('button:has-text("Consultar")') or \
                    await page.query_selector('button:has-text("Buscar")')
            
            if button:
                await button.click()
                print(f"✅ Botão clicado!")
                
                # Aguardar resposta
                print(f"⏳ Aguardando resposta da API...")
                await asyncio.sleep(5)
                
                if captured_response:
                    print()
                    print("=" * 70)
                    print("🎉 SUCESSO TOTAL!")
                    print("=" * 70)
                    print()
                    print(json.dumps(captured_response, indent=2, ensure_ascii=False))
                    print()
                    print("=" * 70)
                    
                    # Salvar
                    with open('/tmp/fazenda_success.json', 'w') as f:
                        json.dump(captured_response, f, indent=2, ensure_ascii=False)
                    print("💾 Salvo em: /tmp/fazenda_success.json")
                    
                    await browser.close()
                    return captured_response
                else:
                    print("⚠️  Resposta não capturada")
                    print("   Aguardando mais tempo...")
                    await asyncio.sleep(5)
                    
                    if captured_response:
                        print("✅ Resposta capturada agora!")
                        await browser.close()
                        return captured_response
            else:
                print("❌ Botão não encontrado")
        else:
            print("❌ Campo de input não encontrado")
        
        print()
        print("⏸️  Pressione ENTER para fechar navegador...")
        input()
        await browser.close()
        
    return None

if __name__ == "__main__":
    result = asyncio.run(test_complete_flow())
    
    if result:
        print()
        print("🎉 TESTE COMPLETO BEM-SUCEDIDO!")
        print()
        print("✅ Próximos passos:")
        print("   - Atualizar fazenda_api_client.py com sitekey correto")
        print("   - Implementar lógica de digitar antes de resolver CAPTCHA")
        print("   - Testar integração no plate_calculator.py")
    else:
        print()
        print("⚠️  Teste não completou - veja logs acima")

"""
Fazenda MG API with 2Captcha Turnstile Integration
Uses 2Captcha's native Turnstile support
"""
import asyncio
import json
import requests
import time
from playwright.async_api import async_playwright

import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('CAPTCHA_API_KEY', '')
FAZENDA_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"
CAPTCHA_API_URL = "https://api.2captcha.com"

async def solve_turnstile_and_query(renavam):
    """
    Solve Cloudflare Turnstile using 2Captcha and query Fazenda API
    """
    async with async_playwright() as p:
        print("🚀 Abrindo navegador...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Capture API responses
        captured_token = None
        captured_response = None
        
        async def handle_response(response):
            nonlocal captured_response
            if '/api/extrato-debito/renavam/' in response.url and response.status == 200:
                try:
                    captured_response = await response.json()
                    print(f"✅ RESPOSTA DA API CAPTURADA!")
                except:
                    pass
        
        page.on('response', handle_response)
        
        print(f"📡 Navegando para {FAZENDA_URL}")
        await page.goto(FAZENDA_URL)
        await asyncio.sleep(3)
        
        # Extract Turnstile parameters using JavaScript injection
        print("🔍 Extraindo parâmetros do Turnstile...")
        
        turnstile_params = await page.evaluate('''() => {
            return new Promise((resolve) => {
                const i = setInterval(() => {
                    if (window.turnstile) {
                        clearInterval(i);
                        const originalRender = window.turnstile.render;
                        window.turnstile.render = (a, b) => {
                            const params = {
                                sitekey: b.sitekey,
                                action: b.action,
                                cData: b.cData,
                                chlPageData: b.chlPageData
                            };
                            window.tsCallback = b.callback;
                            resolve(params);
                            return originalRender(a, b);
                        };
                    }
                }, 100);
                
                // Timeout after 10 seconds
                setTimeout(() => {
                    clearInterval(i);
                    resolve(null);
                }, 10000);
            });
        }''')
        
        if not turnstile_params or not turnstile_params.get('sitekey'):
            print("⚠️ Não conseguiu extrair parâmetros do Turnstile")
            print("Tentando método alternativo...")
            
            # Try to find sitekey in HTML
            sitekey = await page.evaluate('''() => {
                const el = document.querySelector('[data-sitekey]');
                return el ? el.getAttribute('data-sitekey') : null;
            }''')
            
            if sitekey:
                turnstile_params = {'sitekey': sitekey}
                print(f"✅ Sitekey encontrado: {sitekey}")
            else:
                print("❌ Não foi possível encontrar o sitekey")
                await browser.close()
                return None
        else:
            print(f"✅ Parâmetros extraídos:")
            print(f"   Sitekey: {turnstile_params.get('sitekey')}")
            if turnstile_params.get('action'):
                print(f"   Action: {turnstile_params.get('action')}")
        
        # Solve with 2Captcha
        print(f"\n🤖 Resolvendo Turnstile com 2Captcha...")
        
        # Create task
        task_payload = {
            "clientKey": API_KEY,
            "task": {
                "type": "TurnstileTaskProxyless",
                "websiteURL": FAZENDA_URL,
                "websiteKey": turnstile_params['sitekey']
            }
        }
        
        # Add optional parameters if available
        if turnstile_params.get('action'):
            task_payload['task']['action'] = turnstile_params['action']
        if turnstile_params.get('cData'):
            task_payload['task']['data'] = turnstile_params['cData']
        if turnstile_params.get('chlPageData'):
            task_payload['task']['pagedata'] = turnstile_params['chlPageData']
        
        print(f"📤 Enviando task para 2Captcha...")
        create_response = requests.post(
            f"{CAPTCHA_API_URL}/createTask",
            json=task_payload,
            timeout=30
        )
        
        create_result = create_response.json()
        
        if create_result.get('errorId') != 0:
            print(f"❌ Erro ao criar task: {create_result.get('errorDescription')}")
            await browser.close()
            return None
        
        task_id = create_result['taskId']
        print(f"✅ Task criada: {task_id}")
        print(f"⏳ Aguardando resolução (pode levar 10-30 segundos)...")
        
        # Poll for result
        max_attempts = 60
        attempt = 0
        
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
                token = result['solution']['token']
                print(f"\n✅ TURNSTILE RESOLVIDO!")
                print(f"🎫 Token: {token[:50]}...")
                
                # Inject token into page
                print(f"\n💉 Injetando token na página...")
                await page.evaluate(f'''(token) => {{
                    // Set token in hidden input
                    const input = document.querySelector('[name="cf-turnstile-response"]');
                    if (input) {{
                        input.value = token;
                    }}
                    
                    // Call callback if available
                    if (window.tsCallback) {{
                        window.tsCallback(token);
                    }}
                }}''', token)
                
                await asyncio.sleep(1)
                
                # Fill RENAVAM and submit
                print(f"\n⌨️ Preenchendo RENAVAM: {renavam}")
                await page.fill('input[type="text"]', renavam)
                await asyncio.sleep(1)
                
                print(f"🖱️ Clicando em consultar...")
                button = await page.query_selector('button[type="submit"]')
                if button:
                    await button.click()
                    
                    print(f"⏳ Aguardando resposta da API...")
                    await asyncio.sleep(5)
                    
                    if captured_response:
                        print(f"\n🎉 SUCESSO TOTAL!")
                        print("=" * 70)
                        print(json.dumps(captured_response, indent=2, ensure_ascii=False))
                        print("=" * 70)
                        
                        result_data = {
                            'renavam': renavam,
                            'turnstile_token': token,
                            'api_response': captured_response,
                            'cost': result.get('cost', 'unknown')
                        }
                        
                        with open('/tmp/fazenda_final_success.json', 'w') as f:
                            json.dump(result_data, f, indent=2, ensure_ascii=False)
                        
                        print(f"\n💾 Dados salvos em: /tmp/fazenda_final_success.json")
                        print(f"💰 Custo: ${result.get('cost', 'unknown')}")
                        
                        await browser.close()
                        return result_data
                    else:
                        print(f"\n⚠️ Não capturou resposta da API")
                else:
                    print(f"❌ Botão não encontrado")
                
                break
                
            elif result.get('status') == 'processing':
                print(f"   Tentativa {attempt}/{max_attempts}...")
            else:
                print(f"❌ Erro: {result}")
                break
        
        await browser.close()
        return None

if __name__ == "__main__":
    print("=" * 70)
    print("FAZENDA MG API - 2CAPTCHA TURNSTILE (MÉTODO CORRETO)")
    print("=" * 70)
    print()
    
    RENAVAM = "01293554640"
    
    try:
        result = asyncio.run(solve_turnstile_and_query(RENAVAM))
        
        if result:
            print(f"\n✅ INTEGRAÇÃO COMPLETA FUNCIONANDO!")
            print(f"\n🎯 Próximos passos:")
            print(f"   1. Integrar com plate_calculator.py")
            print(f"   2. Adicionar fallback para scraping")
            print(f"   3. Configurar API key no ambiente")
            print(f"   4. Deploy!")
        else:
            print(f"\n⚠️ Não completou - verifique logs acima")
            
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()

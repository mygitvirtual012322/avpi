#!/usr/bin/env python3
"""
Teste FINAL com código otimizado
Usa o método comprovado do fazenda_2captcha_final.py
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
SITEKEY = "0x4AAAAAAAWV7kjZLnydRbx6"
RENAVAM = "01293554640"

async def test_final():
    print("=" * 70)
    print("TESTE FINAL: FAZENDA API + 2CAPTCHA")
    print("=" * 70)
    print()
    
    if not API_KEY:
        print("❌ CAPTCHA_API_KEY não configurada!")
        return None
    
    # Resolver Turnstile
    print("🤖 Resolvendo Turnstile com 2Captcha...")
    task_payload = {
        "clientKey": API_KEY,
        "task": {
            "type": "TurnstileTaskProxyless",
            "websiteURL": FAZENDA_URL,
            "websiteKey": SITEKEY
        }
    }
    
    create_response = requests.post(f"{CAPTCHA_API_URL}/createTask", json=task_payload, timeout=30)
    create_result = create_response.json()
    
    if create_result.get('errorId') != 0:
        print(f"❌ Erro: {create_result.get('errorDescription')}")
        return None
    
    task_id = create_result['taskId']
    print(f"✅ Task: {task_id}")
    print(f"⏳ Aguardando...")
    
    # Poll
    for attempt in range(60):
        await asyncio.sleep(2)
        result_response = requests.post(
            f"{CAPTCHA_API_URL}/getTaskResult",
            json={"clientKey": API_KEY, "taskId": task_id},
            timeout=30
        )
        result = result_response.json()
        
        if result.get('status') == 'ready':
            token = result['solution']['token']
            print(f"✅ Resolvido! Custo: ${result.get('cost')}")
            break
    else:
        print("❌ Timeout")
        return None
    
    # Usar token
    print()
    print("🚀 Consultando API...")
    
    async with async_playwright() as p:
        # Launch com argumentos para mascarar automação
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-infobars', 
                '--start-maximized'
            ]
        )
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # Injetar script stealth
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        captured_response = None
        
        async def handle_response(response):
            nonlocal captured_response
            if '/api/extrato-debito/renavam/' in response.url:
                print(f"📡 Request API detectado: {response.url} [{response.status}]")
                if response.status == 200:
                    try:
                        captured_response = await response.json()
                        print(f"✅ API RESPONDEU (JSON capturado)!")
                    except:
                        print(f"⚠️  API respondeu 200 mas falhou no JSON")
        
        page.on('response', handle_response)
        
        # Intercept Turnstile render
        print("🔍 Configurando interceptação...")
        await page.evaluate('''() => {
            window.turnstileData = {};
            const i = setInterval(() => {
                if (window.turnstile) {
                    clearInterval(i);
                    const originalRender = window.turnstile.render;
                    window.turnstile.render = (container, params) => {
                        console.log('Intercepted:', params);
                        window.tsCallback = params.callback;
                        return originalRender(container, params);
                    };
                }
            }, 50);
        }''')
        
        await page.goto(FAZENDA_URL)
        await asyncio.sleep(2)
        
        # Preencher RENAVAM
        await page.fill('input[type="text"]', RENAVAM)
        print(f"✅ RENAVAM: {RENAVAM}")
        
        # Aguardar Turnstile renderizar e capturar callback
        print("⏳ Aguardando Turnstile...")
        for _ in range(10):
            has_callback = await page.evaluate('() => !!window.tsCallback')
            if has_callback:
                print("✅ Callback capturado!")
                break
            await asyncio.sleep(1)
            
        await asyncio.sleep(1)
        
        # Injetar token e HABILITAR BOTÃO
        print(f"💉 Injetando token...")
        await page.evaluate(f'''(token) => {{
            // 1. Set hidden inputs (both Turnstile and legacy Recaptcha)
            const inputs = document.querySelectorAll('[name="cf-turnstile-response"], [name="g-recaptcha-response"]');
            inputs.forEach(input => input.value = token);
            
            // 2. Call captured callback
            if (window.tsCallback) {{
                console.log('Calling callback...');
                try {{
                    window.tsCallback(token);
                }} catch (e) {{
                    console.error('Error calling callback:', e);
                }}
            }}
            
            // 3. Force enable button (React safe way - triggering events)
            const btn = document.querySelector('button[type="submit"]');
            if (btn) {{
                btn.removeAttribute('disabled');
                btn.classList.remove('disabled');
                
                // Disparar eventos para acordar o React
                btn.dispatchEvent(new Event('change', {{ bubbles: true }}));
                btn.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }}''', token)
        
        await asyncio.sleep(2)
        
        # Clicar
        print(f"🖱️  Clicando...")
        try:
            # Tentar clique via JS Dispatch Event (mais confiável para React)
            await page.evaluate('''() => {
                const btn = document.querySelector('button[type="submit"]');
                if (btn) {
                    const clickEvent = new MouseEvent('click', {
                        view: window,
                        bubbles: true,
                        cancelable: true
                    });
                    btn.dispatchEvent(clickEvent);
                    console.log('Click event dispatched');
                }
            }''')
        except:
             print("❌ Erro no clique JS")

        # Fallback: Submit form direto
        await asyncio.sleep(2)
        if not captured_response:
             print("⚠️  Tentando requestSubmit no form...")
             await page.evaluate('''() => {
                const form = document.querySelector('form');
                if (form) form.requestSubmit();
             }''')
             
        # Fallback 2: FETCH DIRETO no navegador (Bypassing UI)
        await asyncio.sleep(2)
        if not captured_response:
            print("🚀 TENTATIVA FINAL: Fetch direto via JS...")
            api_url = f"https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/api/extrato-debito/renavam/{RENAVAM}/"
            
            # Passando argumentos corretamente (sem f-string para o JS)
            js_script = """(params) => {
                return fetch(params.url, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Token': params.token,
                        'Referer': 'https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/'
                    }
                }).then(res => {
                    if (res.ok) return res.json();
                    return { error: res.status, text: res.statusText };
                }).catch(err => ({ error: err.toString() }));
            }"""
            
            js_result = await page.evaluate(js_script, { 'url': api_url, 'token': token })
            
            print(f"📊 Resultado do fetch direto: {str(js_result)[:300]}...")
            if js_result and 'error' not in js_result:
                captured_response = js_result
                print("✅ SUCESSO via Fetch Direto!")

        # Aguardar resposta
        print(f"⏳ Aguardando API...")
        await asyncio.sleep(8)
        
        if captured_response:
            print()
            print("=" * 70)
            print("🎉 SUCESSO!")
            print("=" * 70)
            print(json.dumps(captured_response, indent=2, ensure_ascii=False))
            print("=" * 70)
            
            with open('/tmp/fazenda_final.json', 'w') as f:
                json.dump(captured_response, f, indent=2, ensure_ascii=False)
            print("💾 Salvo: /tmp/fazenda_final.json")
            
            await browser.close()
            return captured_response
        else:
            print("⚠️  Sem resposta ainda...")
            print("📸 Veja o navegador para debug")
            input("Pressione ENTER...")
            await browser.close()
    
    return None

if __name__ == "__main__":
    result = asyncio.run(test_final())
    
    if result:
        print("\n🎉 FUNCIONOU!")
    else:
        print("\n⚠️  Não completou")

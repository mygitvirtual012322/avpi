"""
Fazenda MG API Client with Cloudflare Turnstile Bypass
Uses Playwright with stealth mode to pass Turnstile automatically
"""
import asyncio
import json
import requests
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

RENAVAM = "01293554640"
FAZENDA_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"

async def query_fazenda_api_with_turnstile(renavam):
    """
    Query Fazenda API bypassing Cloudflare Turnstile
    """
    async with async_playwright() as p:
        print("🚀 Iniciando navegador com stealth mode...")
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo'
        )
        
        page = await context.new_page()
        
        # Apply stealth mode
        await stealth_async(page)
        
        # Capture API calls
        captured_token = None
        captured_response = None
        
        async def handle_request(request):
            nonlocal captured_token
            if '/api/extrato-debito/renavam/' in request.url:
                headers = await request.all_headers()
                if 'token' in headers:
                    captured_token = headers['token']
                    print(f"✅ TOKEN: {captured_token[:40]}...")
        
        async def handle_response(response):
            nonlocal captured_response
            if '/api/extrato-debito/renavam/' in response.url and response.status == 200:
                try:
                    captured_response = await response.json()
                    print(f"✅ RESPOSTA CAPTURADA!")
                except:
                    pass
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        print(f"📡 Navegando para {FAZENDA_URL}")
        await page.goto(FAZENDA_URL, wait_until='networkidle')
        
        print("⏳ Aguardando Turnstile carregar...")
        await asyncio.sleep(3)
        
        # Check if Turnstile passed automatically
        print("🔍 Verificando se Turnstile passou automaticamente...")
        await asyncio.sleep(2)
        
        # Fill RENAVAM
        print(f"⌨️ Preenchendo RENAVAM: {renavam}")
        try:
            await page.fill('input[type="text"]', renavam)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"⚠️ Erro ao preencher: {e}")
        
        # Click submit
        print("🖱️ Clicando em consultar...")
        try:
            button = await page.query_selector('button[type="submit"]')
            if not button:
                button = await page.query_selector('button:has-text("Consultar")')
            if not button:
                button = await page.query_selector('button:has-text("Buscar")')
            
            if button:
                await button.click()
                print("✅ Botão clicado!")
                
                # Wait for response
                print("⏳ Aguardando resposta da API...")
                await asyncio.sleep(5)
                
                if captured_token and captured_response:
                    print("\n🎉 SUCESSO TOTAL!")
                    print("=" * 70)
                    print(json.dumps(captured_response, indent=2, ensure_ascii=False))
                    print("=" * 70)
                    
                    # Save
                    result = {
                        'token': captured_token,
                        'renavam': renavam,
                        'data': captured_response
                    }
                    
                    with open('/tmp/fazenda_api_success.json', 'w') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    
                    print("\n💾 Salvo em: /tmp/fazenda_api_success.json")
                    
                    await browser.close()
                    return result
                else:
                    print(f"\n⚠️ Não capturou dados completos")
                    print(f"Token: {'✅' if captured_token else '❌'}")
                    print(f"Response: {'✅' if captured_response else '❌'}")
                    
                    # Check if Turnstile is blocking
                    turnstile = await page.query_selector('iframe[src*="turnstile"]')
                    if turnstile:
                        print("\n⚠️ Turnstile ainda ativo - pode precisar de interação manual")
                        print("Aguardando 10 segundos para você clicar se necessário...")
                        await asyncio.sleep(10)
                        
                        # Try clicking button again
                        if button:
                            await button.click()
                            await asyncio.sleep(5)
                            
                            if captured_token and captured_response:
                                print("\n🎉 SUCESSO após segunda tentativa!")
                                result = {
                                    'token': captured_token,
                                    'renavam': renavam,
                                    'data': captured_response
                                }
                                with open('/tmp/fazenda_api_success.json', 'w') as f:
                                    json.dump(result, f, indent=2, ensure_ascii=False)
                                await browser.close()
                                return result
            else:
                print("❌ Botão não encontrado")
                
        except Exception as e:
            print(f"❌ Erro ao clicar: {e}")
        
        # Screenshot
        await page.screenshot(path='/tmp/fazenda_final.png')
        print("📸 Screenshot: /tmp/fazenda_final.png")
        
        print("\n⏸️ Pressione ENTER para fechar...")
        input()
        
        await browser.close()
        return None

if __name__ == "__main__":
    print("=" * 70)
    print("FAZENDA MG API - CLOUDFLARE TURNSTILE BYPASS")
    print("=" * 70)
    print()
    
    try:
        result = asyncio.run(query_fazenda_api_with_turnstile(RENAVAM))
        
        if result:
            print("\n✅ API FUNCIONANDO!")
            print("\n🎯 Próximos passos:")
            print("   1. Integrar com plate_calculator.py")
            print("   2. Usar como método primário")
            print("   3. Fallback para scraping se falhar")
        else:
            print("\n⚠️ Não conseguiu desta vez")
            print("💡 Turnstile pode ter pedido verificação manual")
            
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()

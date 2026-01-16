"""
Fazenda MG API Client with 2Captcha Integration
Solves Cloudflare Turnstile using 2Captcha service
"""
import os
import asyncio
import json
import requests
from twocaptcha import TwoCaptcha
from playwright.async_api import async_playwright

# Configuration
FAZENDA_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"
API_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/api/extrato-debito/renavam/{renavam}/"

# 2Captcha API Key (set as environment variable or pass directly)
CAPTCHA_API_KEY = os.getenv('CAPTCHA_API_KEY', '')

class FazendaAPIWith2Captcha:
    """Fazenda MG API client using 2Captcha for Turnstile"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or CAPTCHA_API_KEY
        if not self.api_key:
            raise ValueError("2Captcha API key required. Set CAPTCHA_API_KEY env var or pass api_key parameter")
        
        self.solver = TwoCaptcha(self.api_key)
        print(f"✅ 2Captcha inicializado (saldo será verificado)")
    
    async def solve_turnstile_and_query(self, renavam):
        """
        Solve Turnstile and query API
        """
        async with async_playwright() as p:
            print("🚀 Abrindo navegador...")
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Capture API calls
            captured_token = None
            captured_response = None
            
            async def handle_request(request):
                nonlocal captured_token
                if '/api/extrato-debito/renavam/' in request.url:
                    headers = await request.all_headers()
                    if 'token' in headers:
                        captured_token = headers['token']
                        print(f"✅ Token capturado: {captured_token[:40]}...")
            
            async def handle_response(response):
                nonlocal captured_response
                if '/api/extrato-debito/renavam/' in response.url and response.status == 200:
                    try:
                        captured_response = await response.json()
                        print(f"✅ Resposta capturada!")
                    except:
                        pass
            
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            print(f"📡 Navegando para {FAZENDA_URL}")
            await page.goto(FAZENDA_URL, wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Get Turnstile sitekey
            print("🔍 Procurando Turnstile sitekey...")
            try:
                sitekey = await page.evaluate('''() => {
                    const turnstile = document.querySelector('[data-sitekey]');
                    return turnstile ? turnstile.getAttribute('data-sitekey') : null;
                }''')
                
                if not sitekey:
                    # Try to find in iframe
                    frames = page.frames
                    for frame in frames:
                        if 'turnstile' in frame.url:
                            print(f"✅ Turnstile iframe encontrado: {frame.url}")
                            # Extract sitekey from URL
                            import re
                            match = re.search(r'sitekey=([^&]+)', frame.url)
                            if match:
                                sitekey = match.group(1)
                                break
                
                if sitekey:
                    print(f"✅ Sitekey encontrado: {sitekey}")
                else:
                    print("⚠️ Sitekey não encontrado, usando valor padrão")
                    # Common Cloudflare Turnstile sitekey pattern
                    sitekey = "0x4AAAAAAAxxxxxxxxxx"  # Will need to be updated
                    
            except Exception as e:
                print(f"⚠️ Erro ao buscar sitekey: {e}")
                sitekey = None
            
            if sitekey:
                print(f"\n🤖 Resolvendo Turnstile com 2Captcha...")
                print(f"   Sitekey: {sitekey}")
                print(f"   URL: {FAZENDA_URL}")
                
                try:
                    # Solve Turnstile
                    result = self.solver.turnstile(
                        sitekey=sitekey,
                        url=FAZENDA_URL
                    )
                    
                    turnstile_token = result['code']
                    print(f"✅ Turnstile resolvido! Token: {turnstile_token[:40]}...")
                    
                    # Inject token into page
                    print("💉 Injetando token no Turnstile...")
                    await page.evaluate(f'''(token) => {{
                        const turnstile = document.querySelector('[name="cf-turnstile-response"]');
                        if (turnstile) {{
                            turnstile.value = token;
                        }}
                        // Trigger callback if exists
                        if (window.turnstileCallback) {{
                            window.turnstileCallback(token);
                        }}
                    }}''', turnstile_token)
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"❌ Erro ao resolver Turnstile: {e}")
                    await browser.close()
                    return None
            
            # Fill RENAVAM
            print(f"\n⌨️ Preenchendo RENAVAM: {renavam}")
            try:
                await page.fill('input[type="text"]', renavam)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ Erro ao preencher: {e}")
            
            # Click submit
            print("🖱️ Clicando em consultar...")
            try:
                button = await page.query_selector('button[type="submit"]') or \
                        await page.query_selector('button:has-text("Consultar")') or \
                        await page.query_selector('button:has-text("Buscar")')
                
                if button:
                    await button.click()
                    print("✅ Botão clicado!")
                    
                    # Wait for response
                    print("⏳ Aguardando resposta...")
                    await asyncio.sleep(5)
                    
                    if captured_token and captured_response:
                        print("\n🎉 SUCESSO TOTAL!")
                        print("=" * 70)
                        print(json.dumps(captured_response, indent=2, ensure_ascii=False))
                        print("=" * 70)
                        
                        result = {
                            'token': captured_token,
                            'renavam': renavam,
                            'data': captured_response
                        }
                        
                        with open('/tmp/fazenda_2captcha_success.json', 'w') as f:
                            json.dump(result, f, indent=2, ensure_ascii=False)
                        
                        print("\n💾 Salvo em: /tmp/fazenda_2captcha_success.json")
                        
                        await browser.close()
                        return result
                    else:
                        print(f"\n⚠️ Não capturou dados")
                        print(f"Token: {'✅' if captured_token else '❌'}")
                        print(f"Response: {'✅' if captured_response else '❌'}")
                else:
                    print("❌ Botão não encontrado")
                    
            except Exception as e:
                print(f"❌ Erro: {e}")
            
            await page.screenshot(path='/tmp/fazenda_2captcha.png')
            print("📸 Screenshot: /tmp/fazenda_2captcha.png")
            
            print("\n⏸️ Pressione ENTER para fechar...")
            input()
            
            await browser.close()
            return None


async def test_2captcha_integration(renavam, api_key):
    """Test 2Captcha integration"""
    client = FazendaAPIWith2Captcha(api_key)
    result = await client.solve_turnstile_and_query(renavam)
    
    if result:
        print("\n✅ INTEGRAÇÃO 2CAPTCHA FUNCIONANDO!")
        print("\n📊 Dados obtidos:")
        print(f"   - Token: ✅")
        print(f"   - RENAVAM: {result['renavam']}")
        print(f"   - Dados completos: ✅")
        return result
    else:
        print("\n❌ Falhou - verifique:")
        print("   1. Saldo 2Captcha")
        print("   2. Sitekey correto")
        print("   3. Logs acima")
        return None


if __name__ == "__main__":
    print("=" * 70)
    print("FAZENDA MG API - INTEGRAÇÃO 2CAPTCHA")
    print("=" * 70)
    print()
    
    # Get API key
    api_key = input("Digite sua API Key do 2Captcha: ").strip()
    if not api_key:
        api_key = CAPTCHA_API_KEY
    
    if not api_key:
        print("❌ API Key necessária!")
        exit(1)
    
    renavam = "01293554640"
    
    try:
        result = asyncio.run(test_2captcha_integration(renavam, api_key))
        
        if result:
            print("\n🎯 PRÓXIMOS PASSOS:")
            print("   1. Integrar com plate_calculator.py")
            print("   2. Adicionar fallback para scraping")
            print("   3. Configurar API key no ambiente")
            print("   4. Deploy!")
            
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()

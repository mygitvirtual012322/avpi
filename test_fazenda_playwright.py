"""
Automated test of Fazenda MG API using Playwright
Solves CAPTCHA and queries API with real RENAVAM
"""
import asyncio
import json
import requests
from playwright.async_api import async_playwright

RENAVAM = "01293554640"  # Valid RENAVAM provided by user
FAZENDA_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"
API_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/api/extrato-debito/renavam/{renavam}/"

async def get_captcha_token_and_query():
    """Use Playwright to solve CAPTCHA and get token, then query API"""
    
    async with async_playwright() as p:
        print("🚀 Iniciando navegador...")
        browser = await p.chromium.launch(headless=False)  # headless=False para ver o que está acontecendo
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        print(f"📡 Navegando para {FAZENDA_URL}")
        await page.goto(FAZENDA_URL)
        
        # Wait for page to load
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        print("🔍 Procurando campo de RENAVAM...")
        
        # Try to find RENAVAM input field
        try:
            # Look for input field (might be different selectors)
            renavam_input = await page.wait_for_selector('input[type="text"]', timeout=5000)
            print(f"✅ Campo encontrado, digitando RENAVAM: {RENAVAM}")
            await renavam_input.fill(RENAVAM)
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"⚠️ Erro ao encontrar campo: {e}")
            print("📸 Tirando screenshot para debug...")
            await page.screenshot(path='/tmp/fazenda_page.png')
            print("Screenshot salvo em: /tmp/fazenda_page.png")
        
        print("\n⏸️ PAUSA PARA RESOLVER CAPTCHA MANUALMENTE")
        print("Por favor:")
        print("1. Resolva o CAPTCHA na janela do navegador")
        print("2. Clique em 'Consultar' ou 'Buscar'")
        print("3. Aguarde a resposta aparecer")
        print("\nPressione ENTER aqui quando terminar...")
        
        # Wait for user to solve CAPTCHA manually
        input()
        
        print("\n🔎 Procurando token na requisição...")
        
        # Try to intercept the API call
        token = None
        
        # Listen for API requests
        async def handle_request(request):
            nonlocal token
            if '/api/extrato-debito/renavam/' in request.url:
                headers = await request.all_headers()
                if 'token' in headers:
                    token = headers['token']
                    print(f"✅ Token capturado: {token[:30]}...")
        
        page.on('request', handle_request)
        
        # Wait a bit for the request to happen
        await asyncio.sleep(5)
        
        # Try to extract token from page state
        if not token:
            print("🔍 Tentando extrair token do estado da página...")
            try:
                # Try to get token from Redux state or localStorage
                token = await page.evaluate('''() => {
                    // Try Redux state
                    if (window.__REDUX_STATE__ && window.__REDUX_STATE__.captchaState) {
                        return window.__REDUX_STATE__.captchaState.token;
                    }
                    // Try localStorage
                    const stored = localStorage.getItem('captchaToken');
                    if (stored) return stored;
                    
                    // Try to find in any global variable
                    for (let key in window) {
                        if (key.includes('token') || key.includes('captcha')) {
                            console.log('Found:', key, window[key]);
                        }
                    }
                    return null;
                }''')
                
                if token:
                    print(f"✅ Token extraído: {token[:30]}...")
            except Exception as e:
                print(f"⚠️ Não conseguiu extrair token: {e}")
        
        # Take screenshot of result
        print("📸 Tirando screenshot do resultado...")
        await page.screenshot(path='/tmp/fazenda_result.png')
        print("Screenshot salvo em: /tmp/fazenda_result.png")
        
        # Try to get the response data from the page
        print("\n📊 Tentando extrair dados da resposta...")
        try:
            response_data = await page.evaluate('''() => {
                // Try to find response data in page
                const scripts = document.querySelectorAll('script');
                for (let script of scripts) {
                    if (script.textContent.includes('extratoDebito') || script.textContent.includes('veiculo')) {
                        return script.textContent;
                    }
                }
                return document.body.innerText;
            }''')
            
            print("📄 Dados encontrados na página:")
            print(response_data[:500] if len(response_data) > 500 else response_data)
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair dados: {e}")
        
        print("\n⏸️ Navegador ficará aberto. Pressione ENTER para fechar...")
        input()
        
        await browser.close()
        
        return token

if __name__ == "__main__":
    print("=" * 70)
    print("TESTE AUTOMATIZADO DA API FAZENDA MG")
    print("=" * 70)
    print()
    
    try:
        token = asyncio.run(get_captcha_token_and_query())
        
        if token:
            print(f"\n✅ Token obtido com sucesso!")
            print(f"🔑 Token: {token}")
            
            # Now use the token to query the API
            print(f"\n📡 Consultando API com RENAVAM {RENAVAM}...")
            url = API_URL.format(renavam=RENAVAM)
            
            response = requests.get(
                url,
                headers={'Token': token},
                timeout=30
            )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("\n✅ SUCESSO! Dados completos da API:")
                print("=" * 70)
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print("=" * 70)
                
                # Save to file
                with open('/tmp/fazenda_api_response.json', 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print("\n💾 Resposta salva em: /tmp/fazenda_api_response.json")
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
        else:
            print("\n❌ Não foi possível obter o token")
            
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()

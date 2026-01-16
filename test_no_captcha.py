"""
Test Fazenda API WITHOUT CAPTCHA
Since user reported CAPTCHA doesn't always appear, let's test direct access
"""
import asyncio
import json
import requests
from playwright.async_api import async_playwright

RENAVAM = "01293554640"
FAZENDA_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"
API_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/api/extrato-debito/renavam/{renavam}/"

async def test_direct_access():
    """Test if we can access API without solving CAPTCHA"""
    
    async with async_playwright() as p:
        print("🚀 Abrindo navegador...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Capture token from requests
        captured_token = None
        captured_response = None
        
        async def capture_request(request):
            nonlocal captured_token
            if '/api/extrato-debito/renavam/' in request.url:
                headers = await request.all_headers()
                if 'token' in headers:
                    captured_token = headers['token']
                    print(f"✅ TOKEN CAPTURADO: {captured_token[:40]}...")
        
        async def capture_response(response):
            nonlocal captured_response
            if '/api/extrato-debito/renavam/' in response.url:
                try:
                    data = await response.json()
                    captured_response = data
                    print(f"✅ RESPOSTA CAPTURADA!")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                except:
                    pass
        
        page.on('request', capture_request)
        page.on('response', capture_response)
        
        print(f"📡 Navegando para {FAZENDA_URL}")
        await page.goto(FAZENDA_URL, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Try to find RENAVAM input
        print("🔍 Procurando campo RENAVAM...")
        try:
            # Try to fill RENAVAM
            await page.fill('input[type="text"]', RENAVAM)
            print(f"✅ RENAVAM preenchido: {RENAVAM}")
            await asyncio.sleep(1)
            
            # Look for submit button
            print("🔍 Procurando botão de consulta...")
            button = await page.query_selector('button[type="submit"]') or \
                    await page.query_selector('button:has-text("Consultar")') or \
                    await page.query_selector('button:has-text("Buscar")')
            
            if button:
                print("🖱️ Clicando em consultar...")
                await button.click()
                
                # Wait for response
                print("⏳ Aguardando resposta...")
                await asyncio.sleep(5)
                
                if captured_token and captured_response:
                    print("\n🎉 SUCESSO TOTAL!")
                    print(f"🔑 Token: {captured_token}")
                    print("\n📊 Dados completos:")
                    print("=" * 70)
                    print(json.dumps(captured_response, indent=2, ensure_ascii=False))
                    print("=" * 70)
                    
                    # Save response
                    with open('/tmp/fazenda_success.json', 'w') as f:
                        json.dump({
                            'token': captured_token,
                            'response': captured_response
                        }, f, indent=2, ensure_ascii=False)
                    
                    print("\n💾 Dados salvos em /tmp/fazenda_success.json")
                    
                    await browser.close()
                    return captured_token, captured_response
                else:
                    print("\n⚠️ Não capturou token/resposta")
                    print(f"Token: {captured_token}")
                    print(f"Response: {captured_response}")
            else:
                print("❌ Botão não encontrado")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        # Take screenshot
        await page.screenshot(path='/tmp/fazenda_test.png')
        print("📸 Screenshot: /tmp/fazenda_test.png")
        
        print("\n⏸️ Pressione ENTER para fechar...")
        input()
        
        await browser.close()
        return None, None

if __name__ == "__main__":
    print("=" * 70)
    print("TESTE: API FAZENDA MG SEM CAPTCHA")
    print("=" * 70)
    print()
    
    try:
        token, response = asyncio.run(test_direct_access())
        
        if token and response:
            print("\n✅ CONFIRMADO: API funciona SEM CAPTCHA!")
            print("\n🎯 Isso significa que podemos:")
            print("   1. Usar API oficial diretamente")
            print("   2. Sem custo adicional")
            print("   3. Dados completos (nome proprietário, etc)")
            print("   4. Mais rápido que scraping")
        else:
            print("\n⚠️ Pode precisar de CAPTCHA em alguns casos")
            
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()

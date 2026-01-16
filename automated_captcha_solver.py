"""
AUTOMATED CAPTCHA SOLVER for Fazenda MG
Uses Playwright + OCR to solve CAPTCHA automatically
100% FREE, NO MANUAL INTERVENTION
"""
import asyncio
import json
import requests
import re
from playwright.async_api import async_playwright
from PIL import Image
import io

# Try to import OCR libraries
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    print("⚠️ pytesseract not installed. Install with: pip install pytesseract")
    print("⚠️ Also install tesseract: brew install tesseract (macOS)")
    OCR_AVAILABLE = False

FAZENDA_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"
API_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/api/extrato-debito/renavam/{renavam}/"

class AutomatedCaptchaSolver:
    """Solves Fazenda MG CAPTCHA automatically"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        
    async def solve_captcha_ocr(self, captcha_element):
        """
        Solve CAPTCHA using OCR
        """
        try:
            # Take screenshot of CAPTCHA
            captcha_screenshot = await captcha_element.screenshot()
            
            # Open image with PIL
            image = Image.open(io.BytesIO(captcha_screenshot))
            
            # Preprocess image for better OCR
            # Convert to grayscale
            image = image.convert('L')
            
            # Increase contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Use OCR to read text
            if OCR_AVAILABLE:
                text = pytesseract.image_to_string(image, config='--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                text = text.strip().upper()
                text = re.sub(r'[^A-Z0-9]', '', text)  # Remove non-alphanumeric
                
                print(f"🔍 OCR detectou: '{text}'")
                return text
            else:
                print("❌ OCR não disponível")
                return None
                
        except Exception as e:
            print(f"❌ Erro no OCR: {e}")
            return None
    
    async def get_token_from_api_call(self, renavam):
        """
        Navigate, solve CAPTCHA, and extract token from API call
        """
        async with async_playwright() as p:
            print("🚀 Iniciando navegador...")
            self.browser = await p.chromium.launch(
                headless=False,  # Visible for debugging
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1280, 'height': 720}
            )
            
            self.page = await context.new_page()
            
            # Intercept API calls to capture token
            captured_token = None
            
            async def capture_request(request):
                nonlocal captured_token
                if '/api/extrato-debito/renavam/' in request.url:
                    headers = await request.all_headers()
                    if 'token' in headers:
                        captured_token = headers['token']
                        print(f"✅ Token capturado da requisição: {captured_token[:30]}...")
            
            self.page.on('request', capture_request)
            
            print(f"📡 Navegando para {FAZENDA_URL}")
            await self.page.goto(FAZENDA_URL, wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Try to find and fill RENAVAM field
            print(f"🔍 Procurando campo de RENAVAM...")
            try:
                # Try different selectors
                renavam_input = None
                selectors = [
                    'input[name="renavam"]',
                    'input[placeholder*="RENAVAM"]',
                    'input[type="text"]',
                    'input[id*="renavam"]'
                ]
                
                for selector in selectors:
                    try:
                        renavam_input = await self.page.wait_for_selector(selector, timeout=2000)
                        if renavam_input:
                            print(f"✅ Campo encontrado com selector: {selector}")
                            break
                    except:
                        continue
                
                if renavam_input:
                    await renavam_input.fill(renavam)
                    print(f"✅ RENAVAM digitado: {renavam}")
                    await asyncio.sleep(1)
                else:
                    print("⚠️ Campo de RENAVAM não encontrado automaticamente")
                    
            except Exception as e:
                print(f"⚠️ Erro ao preencher RENAVAM: {e}")
            
            # Try to find CAPTCHA
            print("🔍 Procurando CAPTCHA...")
            try:
                # Look for CAPTCHA image or canvas
                captcha_selectors = [
                    'img[alt*="captcha"]',
                    'img[src*="captcha"]',
                    'canvas',
                    '[data-testid="captcha"]',
                    'img[class*="captcha"]'
                ]
                
                captcha_element = None
                for selector in captcha_selectors:
                    try:
                        captcha_element = await self.page.wait_for_selector(selector, timeout=2000)
                        if captcha_element:
                            print(f"✅ CAPTCHA encontrado: {selector}")
                            break
                    except:
                        continue
                
                if captcha_element:
                    # Try OCR
                    captcha_text = await self.solve_captcha_ocr(captcha_element)
                    
                    if captcha_text:
                        # Find CAPTCHA input field
                        captcha_input = await self.page.query_selector('input[placeholder*="captcha" i]') or \
                                       await self.page.query_selector('input[name*="captcha" i]') or \
                                       await self.page.query_selector('input[type="text"]:not([name="renavam"])')
                        
                        if captcha_input:
                            await captcha_input.fill(captcha_text)
                            print(f"✅ CAPTCHA preenchido: {captcha_text}")
                            await asyncio.sleep(1)
                            
                            # Click submit button
                            submit_button = await self.page.query_selector('button[type="submit"]') or \
                                          await self.page.query_selector('button:has-text("Consultar")') or \
                                          await self.page.query_selector('button:has-text("Buscar")')
                            
                            if submit_button:
                                print("🖱️ Clicando em submit...")
                                await submit_button.click()
                                await asyncio.sleep(3)
                                
                                # Check if we got the token
                                if captured_token:
                                    print(f"🎉 SUCESSO! Token capturado automaticamente!")
                                    await self.browser.close()
                                    return captured_token
                                else:
                                    print("⚠️ Token não foi capturado. CAPTCHA pode estar incorreto.")
                            else:
                                print("⚠️ Botão de submit não encontrado")
                        else:
                            print("⚠️ Campo de entrada do CAPTCHA não encontrado")
                    else:
                        print("❌ OCR falhou em reconhecer o CAPTCHA")
                else:
                    print("⚠️ CAPTCHA não encontrado na página")
                    
            except Exception as e:
                print(f"❌ Erro ao processar CAPTCHA: {e}")
            
            # Take screenshot for debugging
            await self.page.screenshot(path='/tmp/fazenda_debug.png')
            print("📸 Screenshot salvo em /tmp/fazenda_debug.png")
            
            print("\n⚠️ Automação não conseguiu resolver o CAPTCHA")
            print("💡 Possíveis razões:")
            print("   - CAPTCHA muito complexo para OCR")
            print("   - Seletores da página mudaram")
            print("   - CAPTCHA tem proteção anti-bot")
            
            await self.browser.close()
            return None


async def test_automated_solver(renavam):
    """Test the automated solver"""
    solver = AutomatedCaptchaSolver()
    token = await solver.get_token_from_api_call(renavam)
    
    if token:
        print(f"\n✅ Token obtido: {token}")
        
        # Query API
        print(f"\n📡 Consultando API...")
        url = API_URL.format(renavam=renavam)
        response = requests.get(
            url,
            headers={'Token': token},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n🎉 SUCESSO TOTAL! Dados da API:")
            print("=" * 70)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("=" * 70)
            
            with open('/tmp/fazenda_api_response.json', 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("\n💾 Resposta salva em: /tmp/fazenda_api_response.json")
            return data
        else:
            print(f"❌ API retornou erro {response.status_code}: {response.text}")
    else:
        print("\n❌ Não foi possível obter o token automaticamente")
    
    return None


if __name__ == "__main__":
    print("=" * 70)
    print("SOLVER AUTOMÁTICO DE CAPTCHA - FAZENDA MG")
    print("100% GRÁTIS | SEM INTERVENÇÃO MANUAL")
    print("=" * 70)
    print()
    
    RENAVAM = "01293554640"
    
    try:
        result = asyncio.run(test_automated_solver(RENAVAM))
        
        if result:
            print("\n✅ MISSÃO CUMPRIDA!")
        else:
            print("\n⚠️ Automação parcial - pode precisar de ajustes")
            print("💡 Alternativas:")
            print("   1. Melhorar OCR (treinar modelo)")
            print("   2. Usar 2Captcha (pago)")
            print("   3. Manter scraping atual (grátis, funciona)")
            
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()

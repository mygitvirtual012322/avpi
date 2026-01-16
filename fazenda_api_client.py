"""
Fazenda MG Official API Client with 2Captcha Integration
Integrates with the official SEF-MG API using automated CAPTCHA solving
"""
import os
import asyncio
import json
import requests
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
FAZENDA_API_BASE = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br"
FAZENDA_API_ENDPOINT = "/api/extrato-debito/renavam/{renavam}/"
FAZENDA_PAGE_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"
CAPTCHA_API_URL = "https://api.2captcha.com"

# 2Captcha API Key
CAPTCHA_API_KEY = os.getenv('CAPTCHA_API_KEY', '')
DISABLE_2CAPTCHA = os.getenv('DISABLE_2CAPTCHA', 'false').lower() == 'true'

class FazendaAPIClient:
    """Client for Fazenda MG official API with 2Captcha CAPTCHA solving"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or CAPTCHA_API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Origin': FAZENDA_API_BASE,
            'Referer': FAZENDA_PAGE_URL
        })
        
        if not self.api_key and not DISABLE_2CAPTCHA:
            print("⚠️ 2Captcha API key not configured. Set CAPTCHA_API_KEY environment variable.")
    
    async def _solve_turnstile_with_2captcha(self, sitekey: str) -> Optional[str]:
        """
        Solve Cloudflare Turnstile using 2Captcha API
        
        Args:
            sitekey: Turnstile site key
            
        Returns:
            Turnstile token or None if failed
        """
        if not self.api_key:
            print("❌ 2Captcha API key not available")
            return None
        
        try:
            print(f"🤖 Resolvendo Turnstile com 2Captcha...")
            print(f"   Sitekey: {sitekey}")
            
            # Create task
            task_payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "TurnstileTaskProxyless",
                    "websiteURL": FAZENDA_PAGE_URL,
                    "websiteKey": sitekey
                }
            }
            
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
            
            # Poll for result
            max_attempts = 60
            attempt = 0
            
            while attempt < max_attempts:
                await asyncio.sleep(2)
                attempt += 1
                
                result_response = requests.post(
                    f"{CAPTCHA_API_URL}/getTaskResult",
                    json={
                        "clientKey": self.api_key,
                        "taskId": task_id
                    },
                    timeout=30
                )
                
                result = result_response.json()
                
                if result.get('status') == 'ready':
                    token = result['solution']['token']
                    print(f"✅ Turnstile resolvido!")
                    print(f"💰 Custo: ${result.get('cost', 'unknown')}")
                    return token
                    
                elif result.get('status') == 'processing':
                    if attempt % 5 == 0:
                        print(f"   Aguardando... ({attempt}/{max_attempts})")
                else:
                    print(f"❌ Erro: {result}")
                    return None
            
            print(f"❌ Timeout aguardando resolução")
            return None
            
        except Exception as e:
            print(f"❌ Erro ao resolver Turnstile: {e}")
            return None
    
    async def _get_captcha_token_playwright(self, sitekey: str, renavam: str = None) -> Optional[str]:
        """
        Use Playwright to extract sitekey and solve CAPTCHA with 2Captcha.
        Tries to bypass UI issues by fetching data directly in browser context if needed.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("⚠️ Playwright not installed. Install with: pip install playwright && playwright install chromium")
            return None
        
        # Reset last data
        self._last_direct_data = None
        
        # Use known sitekey for Fazenda MG
        if not sitekey:
            sitekey = "0x4AAAAAAAWV7kjZLnydRbx6"
        
        try:
            async with async_playwright() as p:
                print("🚀 Iniciando navegador...")
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                print(f"📡 Navegando para {FAZENDA_PAGE_URL}")
                # Intercept Turnstile render to capture callback
                print("🔍 Configurando interceptação do Turnstile...")
                await page.evaluate('''() => {
                    window.turnstileData = {};
                    const i = setInterval(() => {
                        if (window.turnstile) {
                            clearInterval(i);
                            const originalRender = window.turnstile.render;
                            window.turnstile.render = (container, params) => {
                                console.log('Turnstile render intercepted:', params);
                                window.turnstileData = params;
                                window.tsCallback = params.callback; // Save callback globally
                                return originalRender(container, params);
                            };
                        }
                    }, 50);
                }''')

                # Digitar '1' no campo para ativar Turnstile e disparar o render
                print("⌨️  Digitando no campo RENAVAM para ativar Turnstile...")
                input_field = await page.query_selector('input[type="text"]')
                if input_field:
                    await input_field.fill('1')
                    
                    # Aguardar dados do Turnstile serem capturados
                    print("⏳ Aguardando renderização do Turnstile...")
                    for _ in range(20):
                        data = await page.evaluate('() => window.turnstileData')
                        if data and data.get('sitekey'):
                            sitekey = data.get('sitekey')
                            print(f"✅ Dados Turnstile capturados! Sitekey: {sitekey}")
                            break
                        await asyncio.sleep(0.5)
                
                if not sitekey:
                    print("⚠️  Não capturou via interceptação, usando fallback...")
                    sitekey = "0x4AAAAAAAWV7kjZLnydRbx6"

                print(f"🔑 Usando Sitekey: {sitekey}")
                
                # Solve with 2Captcha
                token = await self._solve_turnstile_with_2captcha(sitekey)
                
                if token:
                    print("💉 Injetando token e forçando botão...")
                    await page.evaluate(f'''(token) => {{
                        // 1. Set hidden input
                        const input = document.querySelector('[name="cf-turnstile-response"]');
                        if (input) {{
                            input.value = token;
                        }}
                        
                        // 2. Remove disabled check from button (FORCE ENABLE)
                        const btn = document.querySelector('button[type="submit"]');
                        if (btn) {{
                            btn.removeAttribute('disabled');
                            btn.classList.remove('disabled');
                            btn.style.pointerEvents = 'auto';
                            btn.style.opacity = '1';
                            console.log('Button enabled manually');
                        }}
                        
                        // 3. Call captured callback
                        if (window.tsCallback) {{
                            console.log('Calling captured Turnstile callback...');
                            window.tsCallback(token);
                        }}
                    }}''', token)
                    
                    # Wait for UI update
                    # Fallback: Fetch direto no contexto do navegador
                    print("🚀 TENTATIVA FINAL: Fetch direto via JS...")
                    api_url = f"https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/api/extrato-debito/renavam/{renavam}/"
                    
                    try:
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
                        
                        js_result = await page.evaluate(js_script, {'url': api_url, 'token': token})
                        
                        if js_result and 'renavam' in js_result:
                            print("✅ SUCESSO via Fetch Direto!")
                            # Salvar resultado em cache temporário ou retornar diretamente?
                            # Como este método deve retornar o TOKEN, na verdade aqui já temos os DADOS.
                            # Precisamos adaptar. O método original retorna TOKEN.
                            # Mas se já temos os dados, seria melhor retornar os DADOS.
                            # No entanto, a arquitetura espera token para fazer o request via Requestssession depois.
                            
                            # Se o fetch funcionou aqui, significa que o token é válido.
                            # O request subsequente via Python Requests deve funcionar também, desde que enviemos os headers corretos.
                            # Vamos retornar o token e deixar o fluxo seguir, mas imprimindo sucesso.
                            
                            # Ou melhor ainda: se conseguimos os dados aqui, poderíamos salvá-los e retornar um token especial ou modificar a arquitetura.
                            # Para manter compatibilidade, vamos confiar que o token funciona e retornar ele.
                            # Mas se o requests falhar depois, perdemos esses dados.
                            
                            # Vamos salvar os dados em um atributo da classe temporariamente
                            self._last_direct_data = js_result
                            return token
                        else:
                            print(f"⚠️ Fetch direto falhou ou retornou erro: {str(js_result)[:100]}")
                            
                    except Exception as e:
                        print(f"❌ Erro no fetch direto: {e}")
                        
                    return token
                
                await browser.close()
                return None
                
        except Exception as e:
            print(f"❌ Erro no Playwright: {e}")
            return None
    
    async def get_vehicle_data_async(self, renavam: str) -> Optional[Dict[str, Any]]:
        """
        Get vehicle data from official API (async version)
        
        Args:
            renavam: Vehicle RENAVAM number
            
        Returns:
            Vehicle data dict or None if failed
        """
        if DISABLE_2CAPTCHA:
            print("⚠️ 2Captcha desabilitado via DISABLE_2CAPTCHA")
            return None
        
        try:
            # Get CAPTCHA token
            print(f"🔐 Obtendo token CAPTCHA para RENAVAM {renavam}...")
            token = await self._get_captcha_token_playwright(sitekey=None)
            
            if not token:
                print("❌ Falha ao obter token CAPTCHA")
                return None
            
            # Call API
            url = FAZENDA_API_BASE + FAZENDA_API_ENDPOINT.format(renavam=renavam)
            print(f"📡 Consultando API da Fazenda: {url}")
            
            response = self.session.get(
                url,
                headers={'Token': token},
                timeout=30
            )
            
            if response.status_code == 401:
                print("❌ Token CAPTCHA inválido ou expirado")
                return None
            
            if response.status_code != 200:
                print(f"❌ API retornou status {response.status_code}")
                return None
            
            data = response.json()
            
            if not data.get('valido'):
                print("⚠️ API retornou dados inválidos")
                return None
            
            print("✅ Dados obtidos da API oficial da Fazenda!")
            return data
            
        except Exception as e:
            print(f"❌ Erro ao consultar API da Fazenda: {e}")
            return None
    
    def get_vehicle_data(self, renavam: str) -> Optional[Dict[str, Any]]:
        """
        Get vehicle data from official API (sync wrapper)
        
        Args:
            renavam: Vehicle RENAVAM number
            
        Returns:
            Vehicle data dict or None if failed
        """
        try:
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.get_vehicle_data_async(renavam))
            loop.close()
            return result
        except Exception as e:
            print(f"❌ Erro ao executar consulta: {e}")
            return None
    
    def get_ipva_by_plate(self, plate: str, renavam: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get IPVA data by plate
        
        Args:
            plate: Vehicle license plate
            renavam: Optional RENAVAM (if already known)
            
        Returns:
            IPVA data dict or None if failed
        """
        if not renavam:
            print(f"⚠️ RENAVAM não fornecido para placa {plate}")
            print("   A API da Fazenda requer RENAVAM. Use scraping para obter RENAVAM primeiro.")
            return None
        
        return self.get_vehicle_data(renavam)


# Global client instance
fazenda_client = FazendaAPIClient()


def get_ipva_data_official(plate: str, renavam: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Try to get IPVA data from official API
    
    Args:
        plate: Vehicle license plate
        renavam: Optional RENAVAM number
        
    Returns:
        IPVA data or None if fails (triggers fallback to scraping)
    """
    return fazenda_client.get_ipva_by_plate(plate, renavam)

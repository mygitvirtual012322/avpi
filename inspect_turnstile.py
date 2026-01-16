#!/usr/bin/env python3
"""
Script para inspecionar a página da Fazenda e encontrar o sitekey do Turnstile
APÓS digitar no campo RENAVAM (Turnstile carrega dinamicamente)
"""
import asyncio
from playwright.async_api import async_playwright

FAZENDA_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"

async def inspect_page_with_typing():
    print("=" * 70)
    print("INSPEÇÃO: Turnstile após digitar RENAVAM")
    print("=" * 70)
    print()
    
    async with async_playwright() as p:
        print("🚀 Abrindo navegador...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print(f"📡 Navegando para {FAZENDA_URL}")
        await page.goto(FAZENDA_URL, wait_until='networkidle')
        await asyncio.sleep(2)
        
        print()
        print("⌨️  Digitando '1' no campo RENAVAM para ativar Turnstile...")
        
        # Encontrar campo de input
        input_field = await page.query_selector('input[type="text"]') or \
                     await page.query_selector('input[name*="renavam"]') or \
                     await page.query_selector('input[placeholder*="RENAVAM"]')
        
        if input_field:
            await input_field.fill('1')
            print("✅ Digitado '1' no campo")
            
            # Aguardar Turnstile carregar
            print("⏳ Aguardando Turnstile carregar...")
            await asyncio.sleep(5)
            
            print()
            print("🔍 Procurando Turnstile sitekey...")
            print()
            
            # Método 1: Procurar por data-sitekey
            sitekey1 = await page.evaluate('''() => {
                const el = document.querySelector('[data-sitekey]');
                return el ? el.getAttribute('data-sitekey') : null;
            }''')
            print(f"Método 1 (data-sitekey): {sitekey1 or '❌ Não encontrado'}")
            
            if sitekey1:
                print()
                print("=" * 70)
                print(f"✅ SITEKEY ENCONTRADO: {sitekey1}")
                print("=" * 70)
            
            # Método 2: Procurar em iframes
            print()
            print("🔍 Procurando em iframes...")
            frames = page.frames
            for i, frame in enumerate(frames):
                url = frame.url[:100]
                print(f"   Frame {i}: {url}...")
                if 'turnstile' in frame.url.lower() or 'cloudflare' in frame.url.lower():
                    print(f"   ✅ Frame Turnstile encontrado!")
                    # Tentar extrair sitekey da URL
                    import re
                    match = re.search(r'sitekey=([^&]+)', frame.url)
                    if match:
                        sitekey2 = match.group(1)
                        print(f"   ✅ Sitekey extraído: {sitekey2}")
            
            # Método 3: Procurar no HTML
            print()
            print("🔍 Procurando no HTML source...")
            html = await page.content()
            import re
            
            patterns = [
                r'data-sitekey="([^"]+)"',
                r'sitekey:\s*["\']([^"\']+)["\']',
                r'siteKey:\s*["\']([^"\']+)["\']',
                r'"sitekey":\s*"([^"]+)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html)
                if matches:
                    print(f"   ✅ Padrão '{pattern}' encontrou: {matches[0]}")
                    break
            else:
                print("   ❌ Nenhum padrão encontrou sitekey")
            
            # Screenshot
            print()
            print("📸 Tirando screenshot...")
            await page.screenshot(path='/tmp/fazenda_with_turnstile.png', full_page=True)
            print("✅ Screenshot salvo em: /tmp/fazenda_with_turnstile.png")
            
        else:
            print("❌ Campo de input não encontrado!")
        
        print()
        print("⏸️  Navegador ficará aberto para inspeção manual.")
        print("   Pressione ENTER para fechar...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_page_with_typing())

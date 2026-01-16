"""
Extract Turnstile sitekey from Cloudflare iframe - MÉTODO DEFINITIVO
"""
import asyncio
from playwright.async_api import async_playwright

async def get_real_sitekey():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("📡 Carregando página...")
        await page.goto('https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/')
        
        print("⏳ Aguardando Turnstile carregar...")
        await asyncio.sleep(5)
        
        # Get all iframes
        print("🔍 Procurando iframe do Turnstile...")
        frames = page.frames
        
        sitekey = None
        for frame in frames:
            url = frame.url
            print(f"   Frame: {url[:80]}...")
            
            if 'challenges.cloudflare.com' in url or 'turnstile' in url.lower():
                print(f"✅ IFRAME DO TURNSTILE ENCONTRADO!")
                print(f"   URL completa: {url}")
                
                # Extract sitekey from URL
                import re
                match = re.search(r'[?&]sitekey=([^&]+)', url)
                if match:
                    sitekey = match.group(1)
                    print(f"\n🎯 SITEKEY EXTRAÍDO: {sitekey}")
                    break
        
        if not sitekey:
            # Try to get from page source
            print("\n🔍 Procurando no HTML da página...")
            content = await page.content()
            
            # Save HTML for manual inspection
            with open('/tmp/page_source.html', 'w') as f:
                f.write(content)
            print("💾 HTML salvo em /tmp/page_source.html")
            
            # Search for sitekey patterns
            import re
            patterns = [
                r'data-sitekey=["\']([^"\']+)["\']',
                r'sitekey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'turnstile.*?sitekey.*?["\']([^"\']+)["\']'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    sitekey = matches[0]
                    print(f"✅ Sitekey encontrado no HTML: {sitekey}")
                    break
        
        print("\n⏸️ Pressione ENTER para fechar...")
        input()
        
        await browser.close()
        return sitekey

if __name__ == "__main__":
    sitekey = asyncio.run(get_real_sitekey())
    
    if sitekey:
        print(f"\n🎉 SITEKEY ENCONTRADO: {sitekey}")
        print(f"\nUse este sitekey no código!")
    else:
        print(f"\n❌ Não encontrou sitekey")
        print(f"Verifique /tmp/page_source.html manualmente")

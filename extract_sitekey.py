#!/usr/bin/env python3
"""
Extrair sitekey do Turnstile e testar com 2Captcha
"""
import asyncio
import re
from playwright.async_api import async_playwright

FAZENDA_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"

async def extract_sitekey():
    print("=" * 70)
    print("EXTRAINDO SITEKEY DO TURNSTILE")
    print("=" * 70)
    print()
    
    async with async_playwright() as p:
        print("🚀 Abrindo navegador...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print(f"📡 Navegando para {FAZENDA_URL}")
        await page.goto(FAZENDA_URL, wait_until='networkidle')
        await asyncio.sleep(2)
        
        print("⌨️  Digitando no campo RENAVAM...")
        input_field = await page.query_selector('input[type="text"]')
        if input_field:
            await input_field.fill('1')
            print("✅ Digitado")
            
            print("⏳ Aguardando Turnstile carregar...")
            await asyncio.sleep(5)
            
            print()
            print("🔍 Procurando sitekey nos iframes...")
            
            frames = page.frames
            sitekey = None
            
            for i, frame in enumerate(frames):
                if 'turnstile' in frame.url.lower() or 'cloudflare' in frame.url.lower():
                    print(f"✅ Frame Turnstile encontrado!")
                    print(f"   URL: {frame.url}")
                    
                    # Extrair sitekey da URL
                    match = re.search(r'/([0-9]x[A-Za-z0-9_-]+)/', frame.url)
                    if match:
                        sitekey = match.group(1)
                        print(f"   ✅ Sitekey extraído: {sitekey}")
                        break
            
            if not sitekey:
                # Tentar método alternativo
                print()
                print("🔍 Tentando método alternativo...")
                sitekey = await page.evaluate('''() => {
                    const el = document.querySelector('[data-sitekey]');
                    return el ? el.getAttribute('data-sitekey') : null;
                }''')
                
                if sitekey:
                    print(f"✅ Sitekey encontrado: {sitekey}")
            
            await browser.close()
            
            if sitekey:
                print()
                print("=" * 70)
                print(f"✅ SITEKEY FINAL: {sitekey}")
                print("=" * 70)
                return sitekey
            else:
                print()
                print("❌ Não conseguiu extrair sitekey")
                return None
        else:
            print("❌ Campo de input não encontrado")
            await browser.close()
            return None

if __name__ == "__main__":
    sitekey = asyncio.run(extract_sitekey())
    
    if sitekey:
        print()
        print("🎯 Próximo passo: testar com 2Captcha")
        print(f"   Sitekey: {sitekey}")
        print(f"   URL: {FAZENDA_URL}")

#!/usr/bin/env python3
"""
DEBUG PROFUNDO: Inspecionar botão e console
"""
import asyncio
from playwright.async_api import async_playwright

FAZENDA_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"

async def debug_button():
    print("=" * 70)
    print("DEBUG: Inspecionando Botão e Console")
    print("=" * 70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Capturar logs do console
        page.on("console", lambda msg: print(f"🖥️  CONSOLE: {msg.text}"))
        page.on("pageerror", lambda err: print(f"❌ ERRO JS: {err}"))
        
        await page.goto(FAZENDA_URL)
        await asyncio.sleep(2)
        
        # Digitar RENAVAM
        await page.fill('input[type="text"]', "01293554640")
        print("✅ RENAVAM preenchido")
        await asyncio.sleep(2)
        
        # Inspecionar botão
        print()
        print("🔍 Inspecionando botão de submit...")
        
        btn_info = await page.evaluate('''() => {
            const btn = document.querySelector('button[type="submit"]');
            if (!btn) return "Botão não encontrado";
            
            return {
                disabled: btn.disabled,
                classes: btn.className,
                style: btn.getAttribute('style'),
                outerHTML: btn.outerHTML,
                hasClick: !!btn.onclick
            };
        }''')
        
        print(f"📊 Estado do botão: {btn_info}")
        
        # Tentar desbloquear manualmente e clicar
        print()
        print("🔓 Tentando desbloquear e clicar...")
        await page.evaluate('''() => {
            const btn = document.querySelector('button[type="submit"]');
            if (btn) {
                btn.removeAttribute('disabled');
                btn.classList.remove('disabled');
                console.log('Botão desbloqueado via JS');
                
                // Adicionar listener para ver se clica
                btn.addEventListener('click', () => console.log('🖱️ CLIQUE DETECTADO NO JS!'));
            }
        }''')
        
        await asyncio.sleep(1)
        
        print("🖱️  Clicando agora...")
        await page.click('button[type="submit"]')
        
        # Screenshot
        await page.screenshot(path='/tmp/debug_fazenda.png')
        print("📸 Screenshot salvo: /tmp/debug_fazenda.png")
        
        print()
        print("⏸️  Pressione ENTER para fechar...")
        input()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_button())

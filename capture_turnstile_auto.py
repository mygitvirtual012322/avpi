"""
SOLUÇÃO DEFINITIVA: Injeta JavaScript ANTES do Turnstile carregar
Captura todos os parâmetros automaticamente
"""
import asyncio
import json
from playwright.async_api import async_playwright

FAZENDA_URL = "https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/"

async def capture_turnstile_params():
    """Captura parâmetros do Turnstile automaticamente"""
    
    async with async_playwright() as p:
        print("🚀 Abrindo navegador...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # JavaScript que será injetado ANTES da página carregar
        intercept_script = """
        console.log("🔍 Interceptor instalado!");
        
        const i = setInterval(() => {
            if (window.turnstile) {
                clearInterval(i);
                console.log("✅ Turnstile encontrado!");
                
                const originalRender = window.turnstile.render;
                window.turnstile.render = (a, b) => {
                    const params = {
                        type: "TurnstileTaskProxyless",
                        websiteKey: b.sitekey,
                        websiteURL: window.location.href,
                        data: b.cData,
                        pagedata: b.chlPageData,
                        action: b.action,
                        userAgent: navigator.userAgent
                    };
                    
                    console.log("🎯 PARÂMETROS CAPTURADOS:");
                    console.log(JSON.stringify(params, null, 2));
                    
                    // Salvar globalmente para Python acessar
                    window.__TURNSTILE_PARAMS__ = params;
                    window.tsCallback = b.callback;
                    
                    return originalRender(a, b);
                };
            }
        }, 10);
        """
        
        # Injetar script ANTES de navegar
        await page.add_init_script(intercept_script)
        
        print(f"📡 Navegando para {FAZENDA_URL}")
        await page.goto(FAZENDA_URL)
        
        print("⏳ Aguardando Turnstile renderizar...")
        await asyncio.sleep(5)
        
        # Tentar extrair parâmetros
        params = await page.evaluate("() => window.__TURNSTILE_PARAMS__")
        
        if params:
            print("\n🎉 PARÂMETROS CAPTURADOS COM SUCESSO!")
            print("=" * 70)
            print(json.dumps(params, indent=2))
            print("=" * 70)
            
            # Salvar em arquivo
            with open('/tmp/turnstile_params.json', 'w') as f:
                json.dump(params, f, indent=2)
            
            print("\n💾 Parâmetros salvos em: /tmp/turnstile_params.json")
            
            await browser.close()
            return params
        else:
            print("\n⚠️ Parâmetros ainda não capturados")
            print("Aguardando mais tempo...")
            
            # Aguardar mais
            for i in range(10):
                await asyncio.sleep(2)
                params = await page.evaluate("() => window.__TURNSTILE_PARAMS__")
                if params:
                    print(f"\n✅ Capturado após {(i+1)*2} segundos!")
                    print(json.dumps(params, indent=2))
                    
                    with open('/tmp/turnstile_params.json', 'w') as f:
                        json.dump(params, f, indent=2)
                    
                    await browser.close()
                    return params
                print(f"   Tentativa {i+1}/10...")
            
            print("\n❌ Não conseguiu capturar parâmetros")
            print("⏸️ Deixando navegador aberto para inspeção manual...")
            print("Pressione ENTER para fechar...")
            input()
            
            await browser.close()
            return None

if __name__ == "__main__":
    print("=" * 70)
    print("CAPTURA AUTOMÁTICA DE PARÂMETROS DO TURNSTILE")
    print("=" * 70)
    print()
    
    params = asyncio.run(capture_turnstile_params())
    
    if params:
        print("\n✅ SUCESSO!")
        print("\nPróximo passo: usar estes parâmetros com 2Captcha")
    else:
        print("\n⚠️ Não capturou automaticamente")
        print("Verifique se o Turnstile está carregando na página")

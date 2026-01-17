# 🚨 Problema: IP da Railway Bloqueado pela Fazenda MG

## Diagnóstico

O sistema está funcionando perfeitamente em localhost (16 segundos), mas trava na Railway.

**Causa Raiz:** O site da Fazenda MG está bloqueando IPs de datacenter (AWS/GCP) onde a Railway hospeda os servidores.

**Evidência no Log:**
```
🚀 Navegando diretamente para API no browser: https://...
[TRAVA AQUI - Timeout no page.goto()]
```

Mesmo usando o navegador Playwright (que passa pelo Captcha), o IP do datacenter é rejeitado.

## ✅ Solução: Proxy Residencial

Para contornar o bloqueio, você precisa configurar um **proxy residencial** que simule um IP doméstico brasileiro.

### Opções de Proxy Recomendadas

1. **Bright Data** (ex-Luminati) - https://brightdata.com
   - Plano gratuito: $5 de crédito
   - IPs residenciais do Brasil
   
2. **Oxylabs** - https://oxylabs.io
   - Trial de 7 dias
   
3. **Smartproxy** - https://smartproxy.com
   - A partir de $8.50/mês

### Como Configurar na Railway

1. **Obtenha as credenciais do proxy** (exemplo Bright Data):
   ```
   Servidor: brd.superproxy.io:22225
   Usuário: brd-customer-XXXXX-zone-residential
   Senha: YYYYYYY
   ```

2. **Configure as variáveis de ambiente na Railway**:
   ```bash
   PROXY_SERVER=http://brd.superproxy.io:22225
   PROXY_USERNAME=brd-customer-XXXXX-zone-residential
   PROXY_PASSWORD=YYYYYYY
   ```

3. **Deploy automático** - A Railway vai redeployar automaticamente

### Testando

Após configurar, o log deve mostrar:
```
🚀 Iniciando navegador...
🔒 Usando proxy: http://brd.superproxy.io:22225
📡 Navegando para https://...
✅ Dados obtidos diretamente pelo navegador!
```

## 🔍 Por que funciona no Localhost?

Seu IP residencial não está na lista de bloqueio da Fazenda MG. Apenas IPs de datacenter são bloqueados.

## 💰 Custo Estimado

- **2Captcha**: $0.00145 por consulta (já configurado)
- **Proxy**: ~$10-20/mês para uso moderado
- **Railway**: Grátis até 500h/mês

**Total**: ~$10-20/mês para operação completa

# INSTRUÇÕES PARA OBTER O SITEKEY DO CLOUDFLARE TURNSTILE

## Método 1: Via DevTools Network

1. Abra: https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/
2. Abra DevTools (F12)
3. Vá na aba **Network**
4. Recarregue a página (Ctrl+R ou Cmd+R)
5. No filtro, digite: `turnstile` ou `cloudflare`
6. Procure por requisições para `challenges.cloudflare.com`
7. Clique na requisição e copie a URL completa
8. O sitekey estará na URL como: `sitekey=XXXXXXXXXX`

## Método 2: Via DevTools Elements

1. Abra: https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/
2. Abra DevTools (F12)
3. Vá na aba **Elements** (ou Inspect)
4. Pressione Ctrl+F (ou Cmd+F) para buscar
5. Procure por: `turnstile` ou `data-sitekey` ou `cloudflare`
6. Encontre o elemento `<iframe>` ou `<div>` com `data-sitekey`
7. Copie o valor do atributo `data-sitekey`

## Método 3: Via Console

1. Abra: https://buscar-renavam-ipva-digital.fazenda.mg.gov.br/buscar-renavam/
2. Abra DevTools (F12)
3. Vá na aba **Console**
4. Cole este código:

```javascript
// Procurar em iframes
document.querySelectorAll('iframe').forEach(iframe => {
    console.log('Iframe src:', iframe.src);
});

// Procurar data-sitekey
document.querySelectorAll('[data-sitekey]').forEach(el => {
    console.log('Sitekey:', el.getAttribute('data-sitekey'));
});
```

5. Copie o sitekey que aparecer

## O que fazer depois

Quando tiver o sitekey, me passe e eu atualizo o código em 2 minutos.

Exemplo de sitekey: `0x4AAAAAAAB...` (começa com 0x4)

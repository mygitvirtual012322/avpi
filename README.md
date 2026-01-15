# Sistema IPVA - Consulta e Pagamento

Sistema web para consulta de IPVA com geração de PIX e tracking completo de conversão.

## 🚀 Deploy no Railway

Este projeto está configurado para deploy automático no Railway com **$5 créditos mensais gratuitos**.

### Deploy Rápido
1. Acesse: https://railway.app
2. Login com GitHub
3. **New Project** → **Deploy from GitHub repo**
4. Selecione: `mygitvirtual012322/avpi`
5. Aguarde 3-5 minutos

Railway vai automaticamente:
- ✅ Instalar Python 3.11
- ✅ Instalar Chromium + Chromedriver
- ✅ Instalar dependências
- ✅ Rodar com Gunicorn (2 workers, 2 threads)

### Recursos Utilizados
- **RAM:** 512MB - 1GB (otimizado para $5 créditos)
- **CPU:** 1-2 vCPUs
- **Custo estimado:** $3-5/mês (dentro dos $5 gratuitos)

## 📋 Features

- ✅ Consulta de placa via scraping (Selenium + Chrome headless)
- ✅ Cálculo automático de IPVA com desconto
- ✅ Geração de código PIX
- ✅ Tracking de conversão (Meta Pixel)
- ✅ Painel administrativo completo
- ✅ Tracking de jornada do usuário
- ✅ Gestão de pedidos

## 🛠️ Stack Tecnológica

- **Backend:** Flask + Gunicorn
- **Scraping:** Selenium + selenium-stealth
- **Browser:** Chromium (headless)
- **Storage:** JSON (admin_data/)
- **Deploy:** Railway (Nixpacks)

## 📁 Estrutura

```
├── server.py              # Servidor Flask
├── plate_calculator.py    # Scraping de placas
├── admin_data_manager.py  # Gestão de dados
├── session_tracker.py     # Tracking de sessões
├── order_manager.py       # Gestão de pedidos
├── meta_pixel.py          # Meta Pixel integration
├── pix_utils.py          # Geração de PIX
├── index.html            # Página principal
├── resultado.html        # Página de resultados
├── admin.html            # Painel admin
├── railway.toml          # Config Railway
├── nixpacks.toml         # Config Nixpacks
└── requirements.txt      # Dependências Python
```

## 🔧 Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar servidor
python server.py

# Acessar
http://localhost:8080
```

## 📊 Monitoramento

Após deploy no Railway:
1. **Logs:** Railway Dashboard → Deployments → View Logs
2. **Uso:** Settings → Usage (ver créditos restantes)
3. **Health:** `https://seu-app.railway.app/api/health`

## ⚙️ Configurações

### Variáveis de Ambiente (Automáticas)
- `PORT` - Porta do servidor (Railway injeta)
- `CHROME_BIN` - Path do Chromium (Nixpacks)
- `CHROMEDRIVER_PATH` - Path do driver (Nixpacks)

### Admin Panel
- URL: `/admin.html`
- Credenciais: Configurar em `admin_auth.py`

## 🎯 Otimizações para Railway

- ✅ Selenium com flags de economia de memória
- ✅ Gunicorn com 2 workers + 2 threads
- ✅ Timeout de 120s para scraping
- ✅ Health check endpoint
- ✅ Auto-restart em caso de falha

## 📝 Notas

- **Selenium:** Funciona perfeitamente com 512MB-1GB RAM no Railway
- **Cloudflare:** Usa `selenium-stealth` para bypass
- **Créditos:** $5/mês cobre uso 24/7 com tráfego leve/médio
- **Scale:** Railway pausa automaticamente se inativo (economiza crédito)

## 🆘 Troubleshooting

### Selenium travando
- Verificar logs: `Railway → Deployments → Logs`
- Aumentar RAM no Railway UI
- Reduzir workers: `--workers 1 --threads 4`

### Timeout na consulta
- Normal: scraping pode levar 10-30s
- Cloudflare bloqueando: verificar logs para "Attention Required"

### Créditos acabando
- Monitorar uso em Settings → Usage
- Otimizar: reduzir workers ou adicionar sleep mode
- Adicionar cartão: paga apenas excedente

## 📄 Licença

Uso privado.

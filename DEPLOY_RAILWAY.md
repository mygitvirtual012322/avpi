# Railway Deployment - $5 Monthly Credits

## ✅ Railway Hobby Plan (Gratuito)

**Recursos incluídos:**
- 💰 **$5 crédito mensal** (renova todo mês)
- 🚀 **Até 8GB RAM / 8 vCPU** por serviço
- 🌍 **Regiões globais**
- 💬 **Suporte comunitário**

**Perfeito para Selenium!** ✅

---

## 📊 Estimativa de Custos

### Configuração Recomendada (Fica nos $5 gratuitos)
- **RAM:** 512MB - 1GB
- **vCPU:** 1-2
- **Custo estimado:** $3-5/mês
- **Uptime:** 24/7 dentro do crédito

### Se precisar mais performance
- **RAM:** 2GB
- **vCPU:** 2
- **Custo:** ~$10/mês (paga $5 extra)

---

## 🚀 Deploy no Railway

### 1. Criar Conta
1. Acesse: https://railway.app
2. Login com GitHub
3. Você ganha **$5 crédito mensal automaticamente**

### 2. Deploy do Projeto
```bash
# No Railway Dashboard
1. New Project
2. Deploy from GitHub repo
3. Selecione: mygitvirtual012322/avpi
4. Railway detecta Python automaticamente
```

### 3. Configuração Automática
Railway vai:
- ✅ Ler `nixpacks.toml` (instala Chromium + Chromedriver)
- ✅ Ler `railway.toml` (configurações de deploy)
- ✅ Instalar dependências do `requirements.txt`
- ✅ Rodar com Gunicorn otimizado

### 4. Variáveis de Ambiente (Automáticas)
Railway injeta automaticamente:
- `PORT` - Porta do servidor
- `RAILWAY_ENVIRONMENT` - Ambiente (production)

Chromium e Chromedriver são instalados via Nixpacks em:
- `/nix/store/.../bin/chromium`
- `/nix/store/.../bin/chromedriver`

---

## ⚙️ Configuração Atual

### `railway.toml`
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn server:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120 --log-level debug"
healthcheckPath = "/api/health"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

**Workers:** 2 workers + 2 threads = ótimo para 512MB-1GB RAM

### `nixpacks.toml`
```toml
[phases.setup]
nixPkgs = ["python311", "chromium", "chromedriver"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "gunicorn server:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120"
```

---

## 📈 Monitoramento de Uso

### Ver Créditos Restantes
1. Railway Dashboard
2. Settings → Usage
3. Veja quanto dos $5 já usou

### Otimizar Custos
Se estiver gastando muito:
1. Reduzir workers: `--workers 1 --threads 4`
2. Adicionar sleep mode (Railway faz automaticamente se inativo)
3. Limitar RAM no Railway UI

---

## ✅ Vantagens do Railway

| Feature | Railway | Render | Fly.io |
|---------|---------|--------|--------|
| **RAM Grátis** | 512MB-1GB ($5) | 512MB | 256MB |
| **Selenium** | ✅ Funciona | ❌ Trava | ❌ Trava |
| **Setup** | Automático | Manual | Manual |
| **Crédito** | $5/mês | - | $5/mês |
| **PostgreSQL** | Pago | Grátis | Pago |

---

## 🎯 Próximos Passos

1. ✅ Código já está configurado
2. ✅ Arquivos `railway.toml` e `nixpacks.toml` prontos
3. 🔄 **Fazer deploy no Railway**
4. 🧪 Testar consulta de placa
5. 📊 Monitorar uso de créditos

---

## 💡 Dicas

- **Scale to Zero:** Railway pausa apps inativos (economiza crédito)
- **Logs em Tempo Real:** Railway → Deployments → View Logs
- **Restart:** Se travar, Railway reinicia automaticamente
- **Custom Domain:** Grátis no Railway

---

## ⚠️ Se Gastar os $5

Opções:
1. **Adicionar cartão:** Paga apenas o excedente (~$3-5/mês)
2. **Otimizar:** Reduzir workers/RAM
3. **Pausar:** Pausar o app quando não usar

**Mas com 512MB-1GB, você fica tranquilo nos $5!** ✅

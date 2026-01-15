# Deploy no Railway

## 🚂 Railway - Trial Gratuito ($5 de crédito)

O Railway oferece $5 de crédito grátis no trial. Você precisa adicionar um cartão, mas não será cobrado até gastar os $5.

---

## 🚀 DEPLOY NO RAILWAY:

### 1. Criar Conta
1. Acesse: https://railway.app
2. Clique em **"Start a New Project"**
3. Faça login com GitHub
4. **Adicione um cartão** (trial de $5 grátis)

### 2. Deploy do GitHub

1. Clique em **"Deploy from GitHub repo"**
2. Selecione: **`mygitvirtual012322/avpi`**
3. Railway vai detectar automaticamente:
   - ✅ `railway.json`
   - ✅ `railway.toml`
   - ✅ `Procfile`
   - ✅ `requirements.txt`

4. Clique em **"Deploy"**

### 3. Configurar Domínio

1. Vá em **"Settings"**
2. Clique em **"Generate Domain"**
3. Seu site estará em: `seu-app.up.railway.app`

### 4. Pronto!

**Site:** `seu-app.up.railway.app`
**Admin:** `seu-app.up.railway.app/admin_new.html`

**Credenciais:**
- User: `admin`
- Pass: `admin2026!`

---

## 📊 Monitoramento

**Ver logs:**
- Na dashboard do Railway, clique em **"Deployments"**
- Clique no deployment ativo
- Veja os logs em tempo real

**Uso de créditos:**
- Dashboard → **"Usage"**
- Mostra quanto dos $5 você já usou

---

## ⚙️ Configuração Automática

O Railway vai usar automaticamente:

**`railway.json`:**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn --bind 0.0.0.0:$PORT --workers 2 server:app"
  }
}
```

**`Procfile`:**
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 server:app
```

---

## 💰 Custos

- **Trial:** $5 grátis (suficiente para ~1 mês)
- **Depois:** ~$5-10/mês dependendo do uso
- **Free tier:** Não existe mais, mas trial é generoso

---

## 🎯 Vantagens do Railway

✅ Deploy automático via GitHub
✅ Logs em tempo real
✅ Fácil de usar
✅ Boa performance
✅ Suporte a variáveis de ambiente

---

## 🔧 Troubleshooting

**Se der erro no build:**
1. Vá em **"Settings"** → **"Environment"**
2. Adicione: `PYTHON_VERSION=3.11`

**Se o site não carregar:**
1. Verifique os logs
2. Certifique-se que a porta está correta (`$PORT`)

---

## 📝 Repositório

**GitHub:** https://github.com/mygitvirtual012322/avpi

**Arquivos de configuração:**
- `railway.json` - Config principal
- `railway.toml` - Config alternativa
- `Procfile` - Comando de start
- `requirements.txt` - Dependências Python
- `server.py` - Flask app

---

**Pronto para deploy! Basta seguir os 4 passos acima.**

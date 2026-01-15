# Deploy no PythonAnywhere (100% GRATUITO)

## 🎯 PythonAnywhere é TOTALMENTE GRÁTIS
- ✅ Sem cartão de crédito
- ✅ Sem limite de tempo
- ✅ 512MB storage
- ✅ Python 3.11 suportado

---

## 🚀 PASSOS PARA DEPLOY:

### 1. Criar Conta
1. Acesse: https://www.pythonanywhere.com
2. Clique em "Start running Python online in less than a minute!"
3. Crie conta gratuita (Beginner account)
4. Confirme email

### 2. Fazer Upload do Código

**Opção A - Via GitHub (Recomendado):**
```bash
# No console do PythonAnywhere (Bash)
git clone https://github.com/mygitvirtual012322/avpi.git
cd avpi
pip3.11 install --user -r requirements.txt
```

**Opção B - Upload Manual:**
1. Vá em "Files"
2. Crie pasta `ipva`
3. Faça upload de todos os arquivos

### 3. Configurar Web App

1. Vá em **"Web"** tab
2. Clique em **"Add a new web app"**
3. Escolha **"Manual configuration"**
4. Selecione **"Python 3.11"**
5. Clique em **"Next"**

### 4. Configurar WSGI

1. Na página Web, clique no link do arquivo WSGI (algo como `/var/www/username_pythonanywhere_com_wsgi.py`)
2. **DELETE TODO** o conteúdo
3. Cole este código:

```python
import sys
import os

# MUDE AQUI: Coloque seu username do PythonAnywhere
project_home = '/home/SEU_USERNAME/avpi'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

os.environ['PORT'] = '8080'

from server import app as application
```

4. **IMPORTANTE:** Substitua `SEU_USERNAME` pelo seu username do PythonAnywhere
5. Clique em **"Save"**

### 5. Configurar Virtualenv (Opcional mas Recomendado)

No console Bash do PythonAnywhere:
```bash
cd ~
python3.11 -m venv venv
source venv/bin/activate
cd avpi
pip install -r requirements.txt
```

Depois, na aba Web, em "Virtualenv", coloque:
```
/home/SEU_USERNAME/venv
```

### 6. Reload e Testar

1. Clique no botão verde **"Reload"** no topo da página Web
2. Clique no link do seu site: `seu-username.pythonanywhere.com`
3. **PRONTO!** Site no ar!

---

## 📋 URLs Após Deploy

**Site:** `seu-username.pythonanywhere.com`
**Admin:** `seu-username.pythonanywhere.com/admin_new.html`

**Credenciais:**
- User: `admin`
- Pass: `admin2026!`

---

## 🔧 Comandos Úteis

**Ver logs:**
```bash
# Na aba Web, clique em "Log files"
# Error log: /var/log/seu-username.pythonanywhere.com.error.log
# Server log: /var/log/seu-username.pythonanywhere.com.server.log
```

**Atualizar código:**
```bash
cd ~/avpi
git pull origin main
# Depois clique em "Reload" na aba Web
```

**Instalar dependências:**
```bash
source ~/venv/bin/activate
cd ~/avpi
pip install -r requirements.txt
```

---

## ⚠️ Limitações Free Tier

- ✅ Site sempre online
- ✅ Sem limite de tempo
- ⚠️ CPU limitada (suficiente para este projeto)
- ⚠️ 512MB storage
- ⚠️ Domínio: `username.pythonanywhere.com` (pode usar domínio próprio no plano pago)

---

## 🎉 Pronto!

Seu sistema IPVA está no ar GRATUITAMENTE e para sempre!

**Repositório:** https://github.com/mygitvirtual012322/avpi

# Deploy no Railway (1GB RAM + PostgreSQL Grátis)

## Por que Railway?
- ✅ **1GB RAM** (suficiente para Selenium + Chrome)
- ✅ **PostgreSQL grátis** incluído
- ✅ **2 vCPUs** para performance
- ✅ **$5 crédito mensal grátis** (sem cartão necessário inicialmente)

## Passo a Passo

### 1. Criar Conta no Railway
1. Acesse: https://railway.app
2. Faça login com GitHub
3. Você ganha **$5 de crédito grátis por mês**

### 2. Criar Novo Projeto
1. Clique em **"New Project"**
2. Selecione **"Deploy from GitHub repo"**
3. Conecte seu repositório: `mygitvirtual012322/avpi`
4. Railway vai detectar automaticamente que é Python

### 3. Adicionar PostgreSQL (Opcional - para futuro)
1. No projeto, clique em **"+ New"**
2. Selecione **"Database"** → **"PostgreSQL"**
3. Railway cria automaticamente e injeta a variável `DATABASE_URL`

### 4. Configurar Variáveis de Ambiente
No painel do Railway, adicione:
```
PORT=8080
CHROME_BIN=/nix/store/.../bin/chromium
CHROMEDRIVER_PATH=/nix/store/.../bin/chromedriver
```

> **Nota:** O Railway com Nixpacks instala automaticamente Chromium e Chromedriver. As variáveis de ambiente são detectadas automaticamente.

### 5. Deploy Automático
- Railway faz deploy automaticamente a cada push no GitHub
- Aguarde ~3-5 minutos para o build completar
- Acesse a URL gerada (ex: `https://seu-app.up.railway.app`)

### 6. Verificar Logs
1. Clique na aba **"Deployments"**
2. Clique no deployment ativo
3. Veja os logs em tempo real

## Diferenças vs Render

| Recurso | Railway (Grátis) | Render (Grátis) |
|---------|------------------|-----------------|
| RAM | **1GB** ✅ | 512MB ❌ |
| CPU | 2 vCPUs | Compartilhado |
| Crédito | $5/mês | Ilimitado (mas lento) |
| PostgreSQL | Incluído ✅ | Separado |
| Build | Nixpacks (rápido) | Docker (lento) |

## Troubleshooting

### Chrome não inicia
Se o Chrome travar, verifique os logs. O Railway tem RAM suficiente, mas pode precisar ajustar workers:
```toml
# railway.toml
startCommand = "gunicorn server:app --workers 1 --threads 4"
```

### Timeout
Aumente o timeout no `railway.toml`:
```toml
startCommand = "gunicorn server:app --timeout 180"
```

### Crédito Acabou
O Railway oferece $5/mês grátis. Se acabar:
- Otimize o uso (menos workers, cache)
- Adicione cartão para continuar (cobra apenas o excedente)

## Próximos Passos (Migração para PostgreSQL)

Quando quiser migrar de JSON para PostgreSQL:
1. Railway já tem PostgreSQL rodando
2. Criar tabelas: `sessions`, `orders`, `config`
3. Migrar código de `admin_data_manager.py` para usar SQLAlchemy
4. Aproveitar a persistência real do banco

**Vantagens do PostgreSQL:**
- ✅ Dados persistem entre deploys
- ✅ Queries mais rápidas
- ✅ Suporta milhares de registros
- ✅ Backup automático no Railway

# Migração para PostgreSQL - Railway

Este guia documenta a migração de JSON para PostgreSQL para compatibilidade com o plano gratuito do Railway.

## Por que PostgreSQL?

Railway mudou a política: **o plano gratuito só funciona com projetos que usam PostgreSQL**.

**Benefícios da migração:**
- ✅ Libera uso gratuito do Railway (1GB RAM + 2 vCPUs)
- ✅ Dados persistem entre deploys
- ✅ Performance superior (queries indexadas)
- ✅ Suporta milhares de registros
- ✅ Backup automático

## Arquitetura

### Antes (JSON)
```
admin_data/
├── config.json
├── consultas.json
├── pix_generated.json
├── user_sessions.json
└── orders.json
```

### Depois (PostgreSQL)
```
PostgreSQL Database:
├── config
├── consultations
├── pix_generated
├── user_sessions
├── orders
└── meta_pixel_config
```

## Tabelas Criadas

### 1. `config`
Configurações do sistema (chave PIX, etc.)

### 2. `consultations`
Histórico de consultas de placas

### 3. `pix_generated`
Códigos PIX gerados

### 4. `user_sessions`
Sessões de usuários com tracking de jornada

### 5. `orders`
Pedidos completos com dados de veículo e pagamento

### 6. `meta_pixel_config`
Configuração do Meta Pixel

## Arquivos Modificados

1. **`database.py`** (NOVO) - Models SQLAlchemy
2. **`requirements.txt`** - Adicionado psycopg2 e sqlalchemy
3. **`server.py`** - Migrado para usar database.py
4. **`admin_data_manager.py`** - Migrado para PostgreSQL
5. **`session_tracker.py`** - Migrado para PostgreSQL
6. **`order_manager.py`** - Migrado para PostgreSQL
7. **`meta_pixel.py`** - Migrado para PostgreSQL

## Deploy no Railway

### 1. Criar Projeto
1. Acesse https://railway.app
2. New Project → Deploy from GitHub
3. Selecione o repositório

### 2. Adicionar PostgreSQL
1. No projeto, clique "+ New"
2. Database → PostgreSQL
3. Railway injeta automaticamente `DATABASE_URL`

### 3. Deploy Automático
- Railway detecta `requirements.txt`
- Instala dependências (incluindo psycopg2)
- Cria tabelas automaticamente no primeiro acesso
- Selenium roda com 1GB RAM ✅

## Variáveis de Ambiente

Railway injeta automaticamente:
- `DATABASE_URL` - URL do PostgreSQL
- `PORT` - Porta do servidor

Não precisa configurar manualmente!

## Desenvolvimento Local

Para testar localmente:

```bash
# Usar SQLite local (sem PostgreSQL)
python server.py
```

O código detecta automaticamente:
- Se `DATABASE_URL` existe → usa PostgreSQL (Railway)
- Se não existe → usa SQLite local (`ipva_local.db`)

## Migração de Dados Existentes

Se você tem dados em JSON que quer migrar:

```python
# Script de migração (executar uma vez)
python migrate_json_to_db.py
```

Isso importa todos os dados de `admin_data/*.json` para o PostgreSQL.

## Verificação

Após deploy, verifique:

1. **Health Check:** `https://seu-app.railway.app/api/health`
2. **Logs:** Railway → Deployments → Ver logs
3. **Database:** Railway → PostgreSQL → Data

## Rollback

Se precisar voltar para JSON:
1. Fazer checkout do commit anterior
2. Remover `database.py` e dependências
3. Restaurar arquivos `admin_data/*.json`

## Performance

**Comparação JSON vs PostgreSQL:**

| Operação | JSON | PostgreSQL |
|----------|------|------------|
| Leitura | ~50ms | ~5ms |
| Escrita | ~100ms | ~10ms |
| Busca | O(n) | O(log n) |
| Concorrência | ❌ | ✅ |

## Próximos Passos

1. ✅ Deploy no Railway
2. ✅ Testar consulta de placas
3. ✅ Verificar admin panel
4. ⏳ Adicionar índices para otimização
5. ⏳ Implementar cache (Redis)

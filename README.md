# Sistema IPVA - Consulta e Pagamento

Sistema completo de consulta de IPVA com desconto de 70%, geração de PIX e admin dashboard em tempo real.

## 🚀 Deploy no Fly.io

### Pré-requisitos
1. Instale o Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Faça login: `fly auth login`

### Deploy
```bash
# Na pasta do projeto
fly launch --no-deploy

# Faça deploy
fly deploy

# Abra o app
fly open
```

## 📋 Funcionalidades

### Frontend
- ✅ Consulta de IPVA por placa e Renavam
- ✅ Cálculo com 70% de desconto
- ✅ Parcelamento em 4x
- ✅ Geração de código PIX
- ✅ QR Code para pagamento

### Admin Dashboard
- ✅ **Live View** com funil de conversão em tempo real
- ✅ Tracking de 3 estágios da jornada:
  - Formulário (inicial)
  - Visualizando resultados
  - Modal PIX (checkout)
- ✅ Detecção de origem (UTM: Facebook/Google/Direct)
- ✅ Lista de usuários online com IP, placa e estágio
- ✅ Gestão completa de pedidos
- ✅ Rastreamento de PIX gerado e copiado
- ✅ Configuração de Meta Pixel ID
- ✅ Atualização automática a cada 2 segundos

### Integrações
- ✅ Meta Pixel com eventos (PageView, InitiateCheckout, Purchase)
- ✅ API de consulta IPVA
- ✅ Geração de PIX dinâmico

## 🔐 Acesso Admin

**URL:** `/admin_new.html`

**Credenciais padrão:**
- Usuário: `admin`
- Senha: `admin2026!`

⚠️ **IMPORTANTE:** Altere as credenciais após o primeiro acesso!

## 🛠️ Tecnologias

- **Backend:** Python 3.11 + Flask + Gunicorn
- **Frontend:** HTML, CSS, JavaScript vanilla
- **Deploy:** Fly.io (Docker)
- **Tracking:** Sistema próprio de sessões
- **Analytics:** Meta Pixel

## 📁 Estrutura

```
├── server.py              # Servidor Flask principal
├── admin.html             # Dashboard admin com live view
├── admin_new.html         # Página de login admin
├── index.html             # Página inicial de consulta
├── resultado.html         # Página de resultados e PIX
├── admin_auth.py          # Sistema de autenticação
├── session_tracker.py     # Tracking de jornada
├── order_manager.py       # Gestão de pedidos
├── meta_pixel.py          # Integração Meta Pixel
├── Dockerfile             # Container para Fly.io
└── fly.toml               # Configuração Fly.io
```

## 🔧 Configuração

### Chave PIX
Edite `config.py`:
```python
PIX_KEY = "sua_chave_pix"
PIX_NAME = "SEU NOME"
PIX_CITY = "SUA CIDADE"
```

### Meta Pixel
Configure no admin: **Meta Pixel** → Digite o ID → Salvar

## 📊 Monitoramento

O admin dashboard mostra em tempo real:
- Quantos usuários em cada etapa do funil
- Lista de usuários online com detalhes
- Pedidos completos com dados do veículo
- Taxa de conversão
- Origem do tráfego (UTM)

## 🚨 Comandos Úteis Fly.io

```bash
# Ver logs
fly logs

# Ver status
fly status

# Abrir dashboard
fly dashboard

# Escalar (se precisar)
fly scale count 1

# Ver secrets
fly secrets list

# Adicionar secret
fly secrets set CHAVE=valor
```

## 📝 Licença

Projeto privado - Todos os direitos reservados

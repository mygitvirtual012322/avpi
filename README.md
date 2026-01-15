# Sistema IPVA - Consulta e Pagamento

Sistema completo de consulta de IPVA com desconto de 70%, geração de PIX e admin dashboard em tempo real.

## 🚀 Deploy no Railway

1. Faça fork ou clone este repositório
2. Crie um novo projeto no [Railway](https://railway.app)
3. Conecte seu repositório GitHub
4. O deploy será automático!

## 📋 Funcionalidades

### Frontend
- ✅ Consulta de IPVA por placa e Renavam
- ✅ Cálculo com 70% de desconto
- ✅ Parcelamento em 4x
- ✅ Geração de código PIX
- ✅ QR Code para pagamento
- ✅ Design profissional e responsivo

### Admin Dashboard
- ✅ **Live View** com funil de conversão em tempo real
- ✅ Tracking de 3 estágios da jornada do usuário:
  - Formulário (inicial)
  - Visualizando resultados
  - Modal PIX (checkout)
- ✅ Detecção de origem (UTM: Facebook/Google/Direct)
- ✅ Lista de usuários online com IP, placa e estágio atual
- ✅ Gestão completa de pedidos com dados do veículo
- ✅ Rastreamento de PIX gerado e copiado
- ✅ Configuração de Meta Pixel ID
- ✅ Atualização automática a cada 2 segundos (sem F5!)

### Integrações
- ✅ Meta Pixel com eventos:
  - PageView (página inicial)
  - InitiateCheckout (gerar PIX)
  - Purchase (copiar código PIX)
- ✅ API de consulta IPVA
- ✅ Geração de PIX dinâmico

## 🔐 Acesso Admin

**URL:** `/admin_new.html`

**Credenciais padrão:**
- Usuário: `admin`
- Senha: `admin2026!`

⚠️ **IMPORTANTE:** Altere as credenciais após o primeiro acesso!

## 🛠️ Tecnologias

- **Backend:** Python (HTTP Server nativo)
- **Frontend:** HTML, CSS, JavaScript vanilla
- **Tracking:** Sistema próprio de sessões
- **Analytics:** Meta Pixel
- **Pagamento:** PIX (geração de payload)

## 📁 Estrutura

```
├── server.py              # Servidor HTTP principal
├── admin.html             # Dashboard admin com live view
├── admin_new.html         # Página de login admin
├── index.html             # Página inicial de consulta
├── resultado.html         # Página de resultados e PIX
├── admin_auth.py          # Sistema de autenticação
├── session_tracker.py     # Tracking de jornada do usuário
├── order_manager.py       # Gestão de pedidos
├── meta_pixel.py          # Integração Meta Pixel
├── plate_calculator.py    # Cálculo de IPVA
├── pix_utils.py           # Geração de código PIX
└── config.py              # Configurações PIX
```

## 🔧 Configuração

### Chave PIX
Edite `config.py` com sua chave PIX:
```python
PIX_KEY = "sua_chave_pix"
PIX_NAME = "SEU NOME"
PIX_CITY = "SUA CIDADE"
```

### Meta Pixel
Configure seu Pixel ID no admin em: **Meta Pixel** → Digite o ID → Salvar

## 📊 Monitoramento

O admin dashboard mostra em tempo real:
- Quantos usuários em cada etapa do funil
- Lista de usuários online com detalhes
- Pedidos completos com dados do veículo
- Taxa de conversão
- Origem do tráfego (UTM)

## 🚨 Segurança

- ✅ Autenticação com hash SHA-256
- ✅ Sessões com tokens únicos
- ✅ Dados sensíveis não versionados (`.gitignore`)
- ✅ Sem credenciais hardcoded no frontend

## 📝 Licença

Projeto privado - Todos os direitos reservados

# Configuração Railway - Axis Gateway

Para garantir que as configurações do Axis persistam entre deploys no Railway, configure as seguintes **variáveis de ambiente**:

## Variáveis de Ambiente

Acesse o painel do Railway → Seu projeto → Variables e adicione:

```
AXIS_ENABLED=true
AXIS_API_KEY=37b6aa3d-f427-4b3c-8384-c2d4848c4c50
AXIS_POSTBACK_URL=https://avpi-production.up.railway.app/api/axis_webhook
```

## Como Configurar

1. Acesse: https://railway.app
2. Selecione seu projeto
3. Clique em "Variables"
4. Adicione cada variável acima
5. Clique em "Deploy" para aplicar

## Verificação

Após configurar, o sistema usará as variáveis de ambiente automaticamente.
O admin mostrará "Source: environment" quando estiver usando env vars.

## Fallback

Se as variáveis de ambiente não estiverem configuradas, o sistema usa o arquivo `admin_data/axis_config.json` (que não persiste no Railway entre deploys).

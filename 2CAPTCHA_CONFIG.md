# Configuração 2Captcha

## Sobre

Este projeto usa o serviço [2Captcha](https://2captcha.com) para resolver automaticamente o Cloudflare Turnstile CAPTCHA da API oficial da Fazenda MG.

## Custo

- **Turnstile CAPTCHA**: ~$0.002 USD por resolução
- **Saldo mínimo recomendado**: $5 USD para ~2.500 consultas

## Configuração

### 1. Obter API Key

1. Acesse: https://2captcha.com/enterpage
2. Faça login ou crie uma conta
3. Copie sua API key do dashboard

### 2. Configurar Variável de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione sua API key:

```env
CAPTCHA_API_KEY=sua_api_key_aqui
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
playwright install chromium
```

## Como Funciona

O sistema usa uma estratégia de múltiplas fontes:

1. **Scraping do ipvabr.com.br** → Obtém dados básicos e RENAVAM
2. **API Oficial da Fazenda MG** → Consulta com 2Captcha (se RENAVAM disponível)
3. **FIPE API** → Fallback se valor venal não disponível

### Fluxo de Dados

```
Placa → ipvabr.com.br (scraping) → RENAVAM
                                  ↓
                        Fazenda API + 2Captcha
                                  ↓
                        Dados oficiais IPVA
```

## Testes

### Testar Saldo 2Captcha

```bash
python -c "from twocaptcha import TwoCaptcha; solver = TwoCaptcha('YOUR_API_KEY'); print(f'Saldo: \${solver.balance()}')"
```

### Testar Integração Completa

```bash
export CAPTCHA_API_KEY=sua_api_key
python test_2captcha_quick.py
```

### Testar via Placa

```bash
python -c "from plate_calculator import calculate_ipva_data; result = calculate_ipva_data('ABC1234'); print(result)"
```

## Desabilitar 2Captcha

Para usar apenas scraping (sem custo):

```env
DISABLE_2CAPTCHA=true
```

## Monitoramento

- **Dashboard 2Captcha**: https://2captcha.com/enterpage
- **Histórico de transações**: Verifique custos e uso
- **Logs do servidor**: Acompanhe qual fonte de dados foi usada

## Troubleshooting

### Erro: "2Captcha API key not configured"

Configure a variável de ambiente `CAPTCHA_API_KEY` no arquivo `.env`

### Erro: "Playwright not installed"

Execute:
```bash
pip install playwright
playwright install chromium
```

### Saldo insuficiente

Adicione créditos em: https://2captcha.com/pay

### API retorna dados inválidos

O sistema automaticamente faz fallback para scraping. Verifique os logs para detalhes.

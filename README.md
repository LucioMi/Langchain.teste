# Agente — LangChain (FastAPI)

Projeto com webhook FastAPI, cadeia simples de IA via LangChain e observabilidade com Langfuse. Integração opcional com Evolution (WhatsApp API) para envio de respostas.

## Requisitos
- Python 3.12+
- Chave de API para IA (`OPENAI_API_KEY`)
- Credenciais do Evolution (se for enviar mensagens): `EVOLUTION_API_BASE_URL`, `EVOLUTION_API_TOKEN`, `EVOLUTION_INSTANCE`
- Credenciais do Langfuse: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`

## Setup
```bash
# 1) Ambiente virtual
python -m venv .venv
source .venv/bin/activate

# 2) Dependências
pip install -r requirements.txt

# 3) Configuração de ambiente
cp .env.example .env
# Edite .env e preencha as variáveis necessárias
```

### Configuração de modelo e prompt (Dia 5)
- Defina o modelo da IA e o prompt do sistema via ambiente:
  - `OPENAI_MODEL` → identificador do modelo da OpenAI
  - `SYSTEM_PROMPT` → texto do prompt do sistema
- Alternativamente, ajuste diretamente em `pyapp/chain.py`.
- Após alterar `.env`, reinicie o servidor para aplicar.

## Executar servidor
```bash
./.venv/bin/python -m uvicorn pyapp.main:app --port 3000
```
- Health: `GET http://127.0.0.1:3000/health` → `{"ok": true}`

## Endpoints de Debug
- Langfuse: `GET http://127.0.0.1:3000/debug/langfuse`
  - Retorna `{ ok, trace_id }`
- Cadeia (LangChain):
  ```bash
  curl "http://127.0.0.1:3000/debug/chain?text=teste"
  ```
  - Retorna `{ ok, reply, usage, context_size, trace_id }`
  - Chamadas sequenciais aumentam `context_size` (memória leve por usuário)

## Webhook
- Endpoint: `POST http://127.0.0.1:3000/webhook/teste.agente.codigo`
- Exemplo:
```bash
curl -X POST "http://127.0.0.1:3000/webhook/teste.agente.codigo" \
  -H "Content-Type: application/json" \
  -d '{
    "message":"oi",
    "sender":"5511999999999@s.whatsapp.net",
    "data":{"key":{"remoteJid":"5511999999999@s.whatsapp.net","id":"abc123"}}
  }'
```
- Resposta: `{ status, reply, sent, error, trace_id }`
  - Se Evolution não estiver corretamente configurado, `sent` pode ser `false` e `error` traz o motivo (ex.: `400 Bad Request`).

## Observabilidade (Langfuse)
- Acesse `LANGFUSE_HOST` (ex.: `https://us.cloud.langfuse.com`).
- Vá em `Observability` → `Traces` e pesquise pelo `trace_id` retornado.
- Spans principais:
  - Debug cadeia: `whatsapp_agent_chain` com `llm_call`
  - Webhook: `whatsapp_agent` com `llm_call` e `evolution_send`

## Notas de Desenvolvimento
- `.gitignore` já exclui itens sensíveis: `.env`, `estudos/`, `.venv`, `__pycache__/`, `node_modules/`, `dist/`, `payload-n8n.json`.
- Não commitar `.env` nem dados privados.
- Ajuste o prompt do sistema em `pyapp/chain.py` conforme o tom desejado.
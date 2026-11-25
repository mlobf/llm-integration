# llm-integration — Ticket Triage

Sistema de triagem de tickets: classifica, prioriza e roteia tickets
automaticamente via API REST (FastAPI). A camada de integração com LLM é
isolada atrás de uma interface e pode rodar em 3 modos: mock em processo,
HTTP contra um provedor mock OpenAI-compatível (Docker), ou HTTP contra um
provedor real (basta trocar `LLM_BASE_URL`/`LLM_API_KEY`).

## Arquitetura

```
app/
├── main.py            # Fábricas (LLM, repositório) + app FastAPI
├── api.py             # Endpoints REST
├── service.py         # Orquestração da triagem (LLM → fallback regras)
├── rules.py           # Motor determinístico de classificação (keywords)
├── storage.py         # TicketRepositoryProtocol + implementação em memória
├── redis_storage.py   # Implementação Redis (persistente, multi-worker)
├── models.py          # Modelos Pydantic (Ticket, TriageResult, enums)
├── config.py          # Configuração via variáveis de ambiente
└── llm/
    ├── base.py        # Contrato da camada LLM (LLMClient, exceções)
    ├── mock.py        # MockLLMClient em processo (sem rede)
    └── openai_client.py # RealLLMClient HTTP (protocolo OpenAI)
services/
└── llm_mock.py        # Provedor LLM fake (OpenAI-compatível) p/ Docker
Dockerfile             # Imagem multi-stage, usuário não-root, healthcheck
docker-compose.yml     # api + redis + llm-mock
.env.example           # Configuração de exemplo (copie para .env)
.github/workflows/ci.yml # CI: testes, build da imagem, smoke test compose
```

### Fluxo de triagem

1. Ticket criado via `POST /tickets`.
2. `TriageService` tenta classificar pela camada LLM (`LLMClient.triage()`).
3. Se a LLM falhar (rede, timeout, resposta inválida) → **fallback** para o
   motor de regras determinístico (`rules.py`).
4. Resultado (`TriageResult`: categoria, prioridade, equipe, confiança,
   resumo) é persistido (memória ou Redis) e o status do ticket atualizado.

### Modos da camada LLM

| `LLM_MODE` | Cliente | Rede? | Uso |
|---|---|---|---|
| `mock` (padrão) | `MockLLMClient` | não | testes unitários, dev rápido |
| `real` + `LLM_BASE_URL` do compose | `RealLLMClient` → `llm-mock` | sim (local) | desenvolvimento Docker, CI |
| `real` + provedor de verdade | `RealLLMClient` → OpenAI etc. | sim | produção (requer `LLM_API_KEY`) |

O `RealLLMClient` fala o protocolo `/v1/chat/completions`. O container
`llm-mock` (`services/llm_mock.py`) simula esse protocolo localmente, sem
custo de API — para usar um provedor real, troque `LLM_BASE_URL` e preencha
`LLM_API_KEY`; nenhum código muda.

## Como rodar

### Com Docker (recomendado — api + redis + llm-mock)

```bash
cp .env.example .env
docker compose up --build
# API em http://localhost:8000 (docs em /docs)
curl localhost:8000/health
```

Os dados persistem no Redis (volume `redis-data`) e sobrevivem a restarts.

### Sem Docker (apenas a API, storage em memória, LLM mock)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

> Com `STORAGE=memory`, use **1 worker**: cada worker teria estado próprio.
> Com `STORAGE=redis`, múltiplos workers são seguros.

### Testes

```bash
.venv/bin/python -m pytest -v            # 26 testes (Redis: 6 skipped sem Redis local)
docker build -t ticket-triage:test .     # build da imagem
docker compose up -d redis               # Redis para os testes de persistência
REDIS_URL_TEST=redis://localhost:6379/0 .venv/bin/python -m pytest tests/test_redis_storage.py -v
```

## API

| Método | Rota                    | Descrição                          |
|--------|-------------------------|------------------------------------|
| GET    | `/health`               | Status, contadores, modo da LLM    |
| POST   | `/tickets`              | Cria ticket e triagem automática   |
| GET    | `/tickets`              | Lista tickets                      |
| GET    | `/tickets/{id}`         | Detalha ticket                     |
| POST   | `/tickets/{id}/triage`  | Reprocessa a triagem               |
| DELETE | `/tickets/{id}`         | Remove ticket                      |

Exemplo:

```bash
curl -X POST localhost:8000/tickets -H 'Content-Type: application/json' \
  -d '{"title":"Fatura cobrada duas vezes","description":"reembolso urgente"}'
```

## Configuração (env)

| Variável              | Padrão                    | Descrição                                   |
|-----------------------|---------------------------|---------------------------------------------|
| `LLM_MODE`            | `mock`                    | `mock` (em processo) ou `real` (HTTP)       |
| `LLM_BASE_URL`        | `http://llm-mock:8001/v1` | Provedor OpenAI-compatível                  |
| `LLM_MODEL`           | `gpt-4o-mini`             | Modelo enviado na requisição                |
| `LLM_API_KEY`         | —                         | Chave do provedor (vazio no mock)           |
| `LLM_TIMEOUT_SECONDS` | `30`                      | Timeout da chamada à LLM                    |
| `STORAGE`             | `memory`                  | `memory` ou `redis`                         |
| `REDIS_URL`           | `redis://redis:6379/0`    | Conexão Redis (host `redis` = compose)      |

## Limitações conhecidas (projeto de estudo)

- Matching de regras por substring (ex.: "download" casa "down" → prioridade alta)
- `GET /tickets` sem paginação
- Sem autenticação/autorização
- `RedisTicketRepository` usa cliente síncrono (bloqueia o event loop
  brevemente; em produção, `redis.asyncio`)

# llm-integration — Ticket Triage

Sistema de triagem de tickets: classifica, prioriza e roteia tickets
automaticamente. **Tudo está implementado, exceto a camada de integração
real com a LLM**, que ficou reduzida a um contrato (interface) + mock,
conforme o escopo.

## Arquitetura

```
app/
├── main.py            # Fábrica do app FastAPI + wiring das dependências
├── api.py             # Endpoints REST
├── service.py         # Orquestração da triagem (LLM → fallback regras)
├── rules.py           # Motor determinístico de classificação (keywords)
├── storage.py         # Repositório em memória (trocável por banco real)
├── models.py          # Modelos Pydantic (Ticket, TriageResult, enums)
├── config.py          # Configuração via variáveis de ambiente
└── llm/
    ├── base.py        # ⚠️ CONTRATO da camada LLM (LLMClient, exceções)
    ├── mock.py        # MockLLMClient — usado em dev/testes (sem rede)
    └── openai_client.py # ⚠️ Stub NÃO implementado (LLM_MODE=real)
```

### Fluxo de triagem

1. Ticket criado via `POST /tickets`.
2. `TriageService` tenta classificar pela camada LLM (`LLMClient.triage()`).
3. Se a LLM falhar ou não estiver configurada → **fallback** para o motor
   de regras determinístico (`rules.py`).
4. Resultado (`TriageResult`: categoria, prioridade, equipe, confiança,
   resumo) é persistido e o ticket muda de status.

### O que falta (fora do escopo)

Implementar `RealLLMClient.triage()` em `app/llm/openai_client.py`:
chamar a API do provedor, converter a resposta em `TriageResult` e levantar
`LLMIntegrationError` em falhas. Nenhum outro arquivo precisa mudar —
o resto do sistema depende só da interface `LLMClient`.

## Como rodar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# testes (22)
.venv/bin/python -m pytest -v

# servidor (http://localhost:8000, docs em /docs)
.venv/bin/uvicorn app.main:app --reload --port 8000
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

| Variável              | Padrão      | Descrição                                  |
|-----------------------|-------------|--------------------------------------------|
| `LLM_MODE`            | `mock`      | `mock` (sem rede) ou `real` (não impl.)    |
| `LLM_MODEL`           | `gpt-4o-mini` | Modelo alvo da integração futura         |
| `LLM_API_KEY`         | —           | Chave do provedor (integração futura)      |
| `LLM_TIMEOUT_SECONDS` | `30`        | Timeout da chamada à LLM                   |

# Ticket Triage — Especificação da Triagem

Especificação do sistema implementado em FastAPI (ver `README.md` para
arquitetura e instruções de execução).

> Nota: uma versão anterior deste arquivo continha uma spec de projeto
> Django + google-genai, que não corresponde ao sistema implementado.
> O conteúdo antigo permanece no histórico do git (commit `a4edb0c`).

## Categorias e roteamento

| Categoria          | Equipe destino | Exemplos de gatilho                        |
|--------------------|----------------|--------------------------------------------|
| `billing`          | billing        | cobrança, fatura, reembolso, assinatura    |
| `access`           | security       | login, senha, 2fa, bloqueado, token        |
| `bug`              | engineering    | erro, falha, crash, exception, 500         |
| `feature_request`  | product        | sugestão, gostaria, melhoria, feature      |
| `question`         | support        | como faço, dúvida, ajuda                   |
| `other`            | support        | sem correspondência                        |

## Prioridades

- `critical`: bug + produção/down → escala imediata
- `high`: urgente, crítico, fora do ar, emergência
- `medium`: padrão
- `low`: "sem pressa", "quando puder"

## Confiança

- Motor de regras: `0.3 + 0.15 × (nº de keywords da categoria)`, teto `0.9`;
  sem correspondência → `0.2`.
- Camada LLM (mock ou HTTP): resultado das regras + `0.1`, teto `0.95`,
  com resumo gerado do ticket.

## Decisão LLM vs. regras

- `LLM_MODE=mock` (padrão): `MockLLMClient` em processo (source `llm`).
- `LLM_MODE=real`: `RealLLMClient` chama `LLM_BASE_URL` (protocolo
  `/v1/chat/completions`). No docker-compose, aponta para o container
  `llm-mock` (provedor fake OpenAI-compatível); para provedor real,
  troque `LLM_BASE_URL` e preencha `LLM_API_KEY`.
- Em falha de rede/timeout/resposta inválida → `LLMIntegrationError` →
  serviço aplica fallback de regras (source `rules`) e incrementa
  `llm_failures` no `/health`.

## Persistência

- `STORAGE=memory` (padrão sem Docker): dados em processo; perde no
  restart; use apenas 1 worker do uvicorn.
- `STORAGE=redis`: `RedisTicketRepository` — JSON por ticket
  (`ticket:{id}`) + sorted set (`tickets:by_created`) para ordenação;
  sobrevive a restarts e permite múltiplos workers.

## Status do ticket

`open` → `triaged` (sem equipe) → `routed` (com equipe) → `closed`

"""Stub da integração real com LLM — INTENCIONALMENTE NÃO IMPLEMENTADO.

Conforme o escopo do projeto, a integração real com o provedor de LLM fica
fora desta entrega. Este arquivo existe para:

1. Documentar onde a integração deve ser plugada.
2. Permitir que `LLM_MODE=real` falhe de forma clara e previsível.

Para implementar:
- herdar de `app.llm.base.LLMClient`;
- chamar a API do provedor em `triage()` (com timeout/ retry);
- converter a resposta em `TriageResult` validado;
- levantar `LLMIntegrationError` em falhas de rede/API.
"""

from __future__ import annotations

from app.llm.base import LLMClient, LLMNotConfiguredError
from app.models import Ticket, TriageResult


class RealLLMClient(LLMClient):
    def __init__(self, api_key: str = "", model: str = "", timeout_seconds: float = 30.0) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def triage(self, ticket: Ticket) -> TriageResult:
        raise LLMNotConfiguredError(
            "Integração real com LLM ainda não foi implementada. "
            "Use LLM_MODE=mock ou implemente RealLLMClient.triage()."
        )

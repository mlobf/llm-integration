"""Mock da camada LLM para desenvolvimento e testes.

Simula o comportamento de um cliente LLM real:
- delega a classificação ao motor de regras (para resultados plausíveis);
- gera um resumo simples;
- permite simular falhas (útil para testar o fallback).

NÃO faz nenhuma chamada de rede.
"""

from __future__ import annotations

import asyncio

from app.llm.base import LLMClient, LLMIntegrationError
from app.models import Ticket, TriageResult
from app.rules import classify_with_rules


class MockLLMClient(LLMClient):
    def __init__(self, latency_seconds: float = 0.0, fail: bool = False) -> None:
        self.latency_seconds = latency_seconds
        self.fail = fail
        self.calls = 0

    async def triage(self, ticket: Ticket) -> TriageResult:
        self.calls += 1
        if self.latency_seconds:
            await asyncio.sleep(self.latency_seconds)
        if self.fail:
            raise LLMIntegrationError("MockLLMClient configurado para falhar")

        result = classify_with_rules(ticket)
        result.source = "llm"
        result.summary = await self.summarize(ticket)
        # Mock é um pouco mais "confiante" que as regras puras.
        result.confidence = min(round(result.confidence + 0.1, 2), 0.95)
        return result

    async def summarize(self, ticket: Ticket) -> str:
        title = ticket.title.strip()
        desc = " ".join(ticket.description.split())
        if len(desc) > 120:
            desc = desc[:117] + "..."
        return f"{title}. {desc}".strip() if desc else title

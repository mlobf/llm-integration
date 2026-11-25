"""Camada de integração com LLM — CONTRATO.

Esta camada é a ÚNICA que conhece o provedor de LLM. O restante do sistema
depende apenas da interface abstrata `LLMClient`.

⚠️  A implementação REAL (OpenAI/Anthropic/etc.) NÃO foi feita — conforme o
escopo, apenas o contrato e um mock. Para integrar de verdade, crie uma
classe (ex.: `app/llm/openai_client.py`) que herde de `LLMClient` e
implemente `triage()`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import Ticket, TriageResult


class LLMIntegrationError(Exception):
    """Erro genérico da integração com LLM (timeout, rate limit, API fora)."""


class LLMNotConfiguredError(LLMIntegrationError):
    """Levantado quando a integração real ainda não foi implementada/configurada."""


class LLMClient(ABC):
    """Interface da camada de integração com LLM."""

    @abstractmethod
    async def triage(self, ticket: Ticket) -> TriageResult:
        """Classifica um ticket (categoria, prioridade, roteamento, resumo).

        Implementações devem levantar LLMIntegrationError em caso de falha,
        para que o serviço possa aplicar o fallback determinístico.
        """
        raise NotImplementedError

    async def summarize(self, ticket: Ticket) -> str:
        """Resumo do ticket em 1-2 frases. Opcional; padrão: sem resumo."""
        return ""

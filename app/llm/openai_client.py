"""Integração real com LLM — cliente HTTP compatível com a API da OpenAI.

Fala o protocolo `/v1/chat/completions` e converte a resposta em
`TriageResult` validado. Por padrão aponta para o mock local
(`services/llm_mock.py`, container `llm-mock`), mas basta trocar
`LLM_BASE_URL` para um provedor real (ex.: https://api.openai.com/v1)
e fornecer `LLM_API_KEY` — nenhum código muda.

Qualquer falha (rede, timeout, resposta inválida) vira
`LLMIntegrationError`, e o `TriageService` aplica o fallback de regras.
"""

from __future__ import annotations

import json
import logging

import httpx

from app.llm.base import LLMClient, LLMIntegrationError
from app.models import Category, Priority, Ticket, TriageResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Você é um sistema de triagem de tickets. Responda SOMENTE com um JSON "
    "contendo: category (bug|billing|access|feature_request|question|other), "
    "priority (critical|high|medium|low), routed_to (equipe), "
    "confidence (0.0-1.0) e summary (1 frase)."
)


class RealLLMClient(LLMClient):
    """Cliente LLM via HTTP (protocolo OpenAI chat completions)."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4o-mini",
        base_url: str = "http://llm-mock:8001/v1",
        timeout_seconds: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._transport = transport  # injetável para testes (ASGITransport)

    def _client(self) -> httpx.AsyncClient:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        kwargs: dict = {
            "base_url": self.base_url,
            "headers": headers,
            "timeout": self.timeout_seconds,
        }
        if self._transport is not None:
            kwargs["transport"] = self._transport
        return httpx.AsyncClient(**kwargs)

    async def triage(self, ticket: Ticket) -> TriageResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": ticket.model_dump_json()},
            ],
            "temperature": 0.0,
        }
        try:
            async with self._client() as client:
                resp = await client.post("/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
        except httpx.HTTPError as exc:
            raise LLMIntegrationError(f"Falha na chamada à LLM: {exc}") from exc
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMIntegrationError(f"Resposta da LLM inválida: {exc}") from exc

        try:
            parsed = json.loads(content)
            return TriageResult(
                category=Category(parsed["category"]),
                priority=Priority(parsed["priority"]),
                routed_to=parsed.get("routed_to"),
                confidence=float(parsed.get("confidence", 0.0)),
                summary=parsed.get("summary"),
                source="llm",
            )
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            raise LLMIntegrationError(f"JSON de triagem inválido: {exc}") from exc

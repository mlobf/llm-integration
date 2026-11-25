"""Testes do RealLLMClient contra o provedor mock (services/llm_mock.py).

Usa httpx.ASGITransport para chamar o app do mock em processo — sem rede,
sem docker. Também cobre os caminhos de falha (fallback do serviço).
"""

import httpx
import pytest

from app.llm.base import LLMIntegrationError
from app.llm.mock import MockLLMClient
from app.llm.openai_client import RealLLMClient
from app.models import Ticket, TicketCreate
from services.llm_mock import app as mock_provider_app


@pytest.fixture
def real_client() -> RealLLMClient:
    transport = httpx.ASGITransport(app=mock_provider_app)
    return RealLLMClient(base_url="http://mock-provider/v1", transport=transport)


def make_ticket(title: str, description: str = "") -> Ticket:
    return Ticket(**TicketCreate(title=title, description=description).model_dump())


@pytest.mark.asyncio
async def test_triage_via_mock_provider(real_client: RealLLMClient):
    ticket = make_ticket("Fatura cobrada duas vezes", "preciso de reembolso urgente")
    result = await real_client.triage(ticket)
    assert result.category.value == "billing"
    assert result.priority.value == "high"
    assert result.routed_to == "billing"
    assert result.source == "llm"
    assert result.summary


@pytest.mark.asyncio
async def test_parity_between_mock_and_real_clients(real_client: RealLLMClient):
    """Mesmo ticket → mesmo resultado pelo MockLLMClient e pelo RealLLMClient
    (ambos usando o motor de regras como 'cérebro')."""
    ticket = make_ticket("Erro 500 no checkout em produção")
    in_process = await MockLLMClient().triage(ticket)
    via_http = await real_client.triage(ticket)
    assert in_process.category == via_http.category
    assert in_process.priority == via_http.priority
    assert in_process.routed_to == via_http.routed_to


@pytest.mark.asyncio
async def test_connection_error_raises_llm_integration_error():
    """Sem provedor no ar → LLMIntegrationError (serviço faz fallback)."""
    client = RealLLMClient(base_url="http://127.0.0.1:1/v1", timeout_seconds=1)
    with pytest.raises(LLMIntegrationError):
        await client.triage(make_ticket("qualquer coisa"))


@pytest.mark.asyncio
async def test_invalid_response_raises_llm_integration_error():
    """Resposta fora do formato OpenAI → LLMIntegrationError."""

    class BrokenTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(200, json={"unexpected": "shape"})

    client = RealLLMClient(base_url="http://x/v1", transport=BrokenTransport())
    with pytest.raises(LLMIntegrationError):
        await client.triage(make_ticket("x"))

import pytest

from app.llm.mock import MockLLMClient
from app.models import TicketCreate
from app.service import TriageService
from app.storage import TicketRepository


@pytest.fixture
def service() -> TriageService:
    return TriageService(TicketRepository(), MockLLMClient())


@pytest.mark.asyncio
async def test_create_ticket_triages_automatically(service: TriageService):
    ticket = await service.create_ticket(
        TicketCreate(title="Cobrança duplicada", description="Fatura cobrada duas vezes")
    )
    assert ticket.status.value == "routed"
    assert ticket.triage is not None
    assert ticket.triage.category.value == "billing"
    assert ticket.triage.source == "llm"


@pytest.mark.asyncio
async def test_llm_failure_falls_back_to_rules():
    service = TriageService(TicketRepository(), MockLLMClient(fail=True))
    ticket = await service.create_ticket(TicketCreate(title="Erro 500 em produção"))
    assert ticket.triage is not None
    assert ticket.triage.source == "rules"
    assert ticket.triage.category.value == "bug"
    assert service.llm_failures == 1


@pytest.mark.asyncio
async def test_without_llm_client_uses_rules():
    service = TriageService(TicketRepository(), llm_client=None)
    ticket = await service.create_ticket(TicketCreate(title="Sugestão de melhoria"))
    assert ticket.triage.source == "rules"
    assert ticket.triage.category.value == "feature_request"


@pytest.mark.asyncio
async def test_retriage(service: TriageService):
    ticket = await service.create_ticket(TicketCreate(title="ticket x"))
    updated = await service.triage_ticket(ticket.id)
    assert updated.triage is not None


@pytest.mark.asyncio
async def test_retriage_missing_raises(service: TriageService):
    with pytest.raises(KeyError):
        await service.triage_ticket("não-existe")


@pytest.mark.asyncio
async def test_list_and_delete(service: TriageService):
    t1 = await service.create_ticket(TicketCreate(title="um"))
    await service.create_ticket(TicketCreate(title="dois"))
    assert len(service.list_tickets()) == 2
    assert service.get_ticket(t1.id).title == "um"
    assert service.delete_ticket(t1.id) is True
    assert service.delete_ticket(t1.id) is False

"""Testes do RedisTicketRepository.

Rodam apenas se houver um Redis acessível em REDIS_URL
(padrão localhost:6379 — ex.: `docker compose up redis`).
Caso contrário, são pulados.
"""

import os

import pytest
import redis

from app.models import Ticket, TicketCreate
from app.redis_storage import RedisTicketRepository
from app.service import TriageService

REDIS_URL = os.getenv("REDIS_URL_TEST", "redis://localhost:6379/0")


def _redis_available() -> bool:
    try:
        r = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1)
        r.ping()
        return True
    except Exception:  # noqa: BLE001 - qualquer falha = Redis indisponível
        return False


pytestmark = pytest.mark.skipif(not _redis_available(), reason="Redis indisponível")


@pytest.fixture
def repo() -> RedisTicketRepository:
    repository = RedisTicketRepository(redis_url=REDIS_URL)
    repository.clear()
    yield repository
    repository.clear()


def make_ticket(title: str = "t") -> Ticket:
    return Ticket(**TicketCreate(title=title).model_dump())


def test_add_and_get(repo: RedisTicketRepository):
    t = repo.add(make_ticket("ticket redis"))
    got = repo.get(t.id)
    assert got is not None
    assert got.title == "ticket redis"


def test_list_is_newest_first(repo: RedisTicketRepository):
    import time

    t1 = repo.add(make_ticket("primeiro"))
    time.sleep(0.01)
    t2 = repo.add(make_ticket("segundo"))
    listed = repo.list()
    assert [t.id for t in listed] == [t2.id, t1.id]


def test_update_changes_updated_at(repo: RedisTicketRepository):
    t = repo.add(make_ticket())
    before = t.updated_at
    t.title = "novo título"
    updated = repo.update(t)
    assert repo.get(updated.id).title == "novo título"
    assert updated.updated_at >= before


def test_delete(repo: RedisTicketRepository):
    t = repo.add(make_ticket())
    assert repo.delete(t.id) is True
    assert repo.delete(t.id) is False
    assert repo.get(t.id) is None


def test_count_and_clear(repo: RedisTicketRepository):
    repo.add(make_ticket("a"))
    repo.add(make_ticket("b"))
    assert repo.count() == 2
    repo.clear()
    assert repo.count() == 0
    assert repo.list() == []


@pytest.mark.asyncio
async def test_service_with_redis_repository(repo: RedisTicketRepository):
    """O TriageService funciona sem alterações com o repositório Redis."""
    service = TriageService(repo, llm_client=None)
    ticket = await service.create_ticket(TicketCreate(title="Cobrança duplicada"))
    assert ticket.triage is not None
    assert ticket.triage.category.value == "billing"
    # Persistiu de verdade
    assert repo.get(ticket.id).triage.category.value == "billing"

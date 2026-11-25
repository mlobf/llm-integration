"""Repositórios de tickets.

`TicketRepositoryProtocol` define o contrato de persistência; o restante do
sistema (service/api) depende apenas dele. Implementações:

- `TicketRepository`       — em memória (padrão, dev/testes)
- `RedisTicketRepository`  — Redis (app/redis_storage.py; sobrevive a restart
                             e permite múltiplos workers)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from app.models import Ticket


class TicketRepositoryProtocol(ABC):
    """Contrato de persistência de tickets."""

    @abstractmethod
    def add(self, ticket: Ticket) -> Ticket: ...

    @abstractmethod
    def get(self, ticket_id: str) -> Ticket | None: ...

    @abstractmethod
    def list(self) -> list[Ticket]: ...

    @abstractmethod
    def update(self, ticket: Ticket) -> Ticket: ...

    @abstractmethod
    def delete(self, ticket_id: str) -> bool: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def clear(self) -> None: ...


class TicketRepository(TicketRepositoryProtocol):
    """Implementação em memória.

    Limitações (ver auditoria D6): dados perdidos no restart e estado
    divergente com múltiplos workers do uvicorn. Use Redis em produção.
    """

    def __init__(self) -> None:
        self._tickets: dict[str, Ticket] = {}

    def add(self, ticket: Ticket) -> Ticket:
        self._tickets[ticket.id] = ticket
        return ticket

    def get(self, ticket_id: str) -> Ticket | None:
        return self._tickets.get(ticket_id)

    def list(self) -> list[Ticket]:
        return sorted(self._tickets.values(), key=lambda t: t.created_at, reverse=True)

    def update(self, ticket: Ticket) -> Ticket:
        ticket.updated_at = datetime.now(UTC)
        self._tickets[ticket.id] = ticket
        return ticket

    def delete(self, ticket_id: str) -> bool:
        return self._tickets.pop(ticket_id, None) is not None

    def count(self) -> int:
        return len(self._tickets)

    def clear(self) -> None:
        self._tickets.clear()

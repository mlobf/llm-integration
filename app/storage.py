"""Repositório em memória para tickets.

Interface simples de CRUD; pode ser trocado por um banco real (SQLite/Postgres)
sem afetar o restante do sistema.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.models import Ticket


class TicketRepository:
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
        ticket.updated_at = datetime.now(timezone.utc)
        self._tickets[ticket.id] = ticket
        return ticket

    def delete(self, ticket_id: str) -> bool:
        return self._tickets.pop(ticket_id, None) is not None

    def count(self) -> int:
        return len(self._tickets)

    def clear(self) -> None:
        self._tickets.clear()

"""Repositório de tickets em Redis.

Persistência: cada ticket é um JSON na chave `ticket:{id}`; um sorted set
`tickets:by_created` mantém a ordenação por data de criação (mais novo
primeiro na listagem).

Nota: usa o cliente síncrono do redis-py. Em um app FastAPI isso bloqueia o
event loop brevemente a cada operação — aceitável para este projeto de estudo;
em produção, prefira `redis.asyncio` com métodos `async`.
"""

from __future__ import annotations

from datetime import UTC, datetime

import redis

from app.models import Ticket
from app.storage import TicketRepositoryProtocol

_KEY_PREFIX = "ticket:"
_INDEX_KEY = "tickets:by_created"


class RedisTicketRepository(TicketRepositoryProtocol):
    def __init__(self, redis_url: str = "redis://redis:6379/0") -> None:
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def _key(self, ticket_id: str) -> str:
        return f"{_KEY_PREFIX}{ticket_id}"

    def _write(self, ticket: Ticket) -> Ticket:
        pipe = self._redis.pipeline()
        pipe.set(self._key(ticket.id), ticket.model_dump_json())
        # score negativo: ZRANGE crescente retorna do mais novo para o mais velho
        pipe.zadd(_INDEX_KEY, {ticket.id: -ticket.created_at.timestamp()})
        pipe.execute()
        return ticket

    def add(self, ticket: Ticket) -> Ticket:
        return self._write(ticket)

    def get(self, ticket_id: str) -> Ticket | None:
        raw = self._redis.get(self._key(ticket_id))
        return Ticket.model_validate_json(raw) if raw else None

    def list(self) -> list[Ticket]:
        ids = self._redis.zrange(_INDEX_KEY, 0, -1)
        if not ids:
            return []
        keys = [self._key(i) for i in ids]
        raws = self._redis.mget(keys)
        return [Ticket.model_validate_json(r) for r in raws if r]

    def update(self, ticket: Ticket) -> Ticket:
        ticket.updated_at = datetime.now(UTC)
        return self._write(ticket)

    def delete(self, ticket_id: str) -> bool:
        pipe = self._redis.pipeline()
        pipe.delete(self._key(ticket_id))
        pipe.zrem(_INDEX_KEY, ticket_id)
        deleted, _ = pipe.execute()
        return bool(deleted)

    def count(self) -> int:
        return int(self._redis.zcard(_INDEX_KEY))

    def clear(self) -> None:
        ids = self._redis.zrange(_INDEX_KEY, 0, -1)
        pipe = self._redis.pipeline()
        if ids:
            pipe.delete(*(self._key(i) for i in ids))
        pipe.delete(_INDEX_KEY)
        pipe.execute()

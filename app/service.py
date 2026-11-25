"""Serviço de triagem — orquestra criação, classificação e roteamento.

Fluxo:
1. Tenta classificar via camada LLM (se disponível).
2. Em falha/indisponibilidade da LLM, aplica fallback determinístico (rules).
3. Persiste o resultado e atualiza o status do ticket.
"""

from __future__ import annotations

import logging

from app.llm.base import LLMClient, LLMIntegrationError
from app.models import Ticket, TicketCreate, TicketStatus, TriageResult
from app.rules import classify_with_rules
from app.storage import TicketRepositoryProtocol

logger = logging.getLogger(__name__)


class TriageService:
    def __init__(self, repository: TicketRepositoryProtocol, llm_client: LLMClient | None = None) -> None:
        self.repository = repository
        self.llm_client = llm_client
        self.llm_failures = 0

    async def _classify(self, ticket: Ticket) -> TriageResult:
        if self.llm_client is not None:
            try:
                return await self.llm_client.triage(ticket)
            except LLMIntegrationError as exc:
                self.llm_failures += 1
                logger.warning("LLM falhou (%s); usando fallback de regras.", exc)
        return classify_with_rules(ticket)

    async def create_ticket(self, payload: TicketCreate) -> Ticket:
        ticket = Ticket(**payload.model_dump())
        self.repository.add(ticket)
        return await self.triage_ticket(ticket.id)

    async def triage_ticket(self, ticket_id: str) -> Ticket:
        ticket = self.repository.get(ticket_id)
        if ticket is None:
            raise KeyError(f"Ticket não encontrado: {ticket_id}")

        result = await self._classify(ticket)
        ticket.triage = result
        ticket.status = TicketStatus.ROUTED if result.routed_to else TicketStatus.TRIAGED
        return self.repository.update(ticket)

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        return self.repository.get(ticket_id)

    def list_tickets(self) -> list[Ticket]:
        return self.repository.list()

    def delete_ticket(self, ticket_id: str) -> bool:
        return self.repository.delete(ticket_id)

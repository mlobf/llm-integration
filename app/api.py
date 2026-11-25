"""Endpoints REST da API de triagem de tickets."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models import Ticket, TicketCreate
from app.service import TriageService

router = APIRouter()


def _service(request: Request) -> TriageService:
    return request.app.state.service


@router.get("/health")
async def health(request: Request) -> dict:
    service = _service(request)
    return {
        "status": "ok",
        "tickets": service.repository.count(),
        "llm_mode": request.app.state.settings.llm_mode,
        "llm_failures": service.llm_failures,
    }


@router.post("/tickets", response_model=Ticket, status_code=201)
async def create_ticket(payload: TicketCreate, request: Request) -> Ticket:
    return await _service(request).create_ticket(payload)


@router.get("/tickets", response_model=list[Ticket])
async def list_tickets(request: Request) -> list[Ticket]:
    return _service(request).list_tickets()


@router.get("/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str, request: Request) -> Ticket:
    ticket = _service(request).get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    return ticket


@router.post("/tickets/{ticket_id}/triage", response_model=Ticket)
async def retriage_ticket(ticket_id: str, request: Request) -> Ticket:
    try:
        return await _service(request).triage_ticket(ticket_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")


@router.delete("/tickets/{ticket_id}", status_code=204)
async def delete_ticket(ticket_id: str, request: Request) -> None:
    if not _service(request).delete_ticket(ticket_id):
        raise HTTPException(status_code=404, detail="Ticket não encontrado")

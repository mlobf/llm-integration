"""Modelos de dados do sistema de triagem de tickets."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(str, Enum):
    BUG = "bug"
    BILLING = "billing"
    ACCESS = "access"
    FEATURE_REQUEST = "feature_request"
    QUESTION = "question"
    OTHER = "other"


class TicketStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    ROUTED = "routed"
    CLOSED = "closed"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class TicketCreate(BaseModel):
    """Payload para criação de um ticket."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10_000)
    requester: str = Field(default="anonymous", max_length=100)
    tags: list[str] = Field(default_factory=list)


class TriageResult(BaseModel):
    """Resultado da triagem de um ticket."""

    category: Category = Category.OTHER
    priority: Priority = Priority.MEDIUM
    routed_to: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    summary: str | None = None
    source: str = "rules"  # "rules" | "llm"


class Ticket(BaseModel):
    """Ticket completo, com estado de triagem."""

    id: str = Field(default_factory=_new_id)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    status: TicketStatus = TicketStatus.OPEN
    title: str
    description: str = ""
    requester: str = "anonymous"
    tags: list[str] = Field(default_factory=list)
    triage: TriageResult | None = None

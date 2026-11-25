"""Ponto de entrada da aplicação FastAPI."""

from __future__ import annotations

from fastapi import FastAPI

from app.api import router
from app.config import Settings, get_settings
from app.llm.base import LLMClient
from app.llm.mock import MockLLMClient
from app.llm.openai_client import RealLLMClient
from app.service import TriageService
from app.storage import TicketRepository


def build_llm_client(settings: Settings) -> LLMClient:
    """Fábrica da camada LLM.

    - "mock": MockLLMClient (sem rede).
    - "real": RealLLMClient — ainda não implementado; falha com
      LLMNotConfiguredError e o serviço cai no fallback de regras.
    """
    if settings.llm_mode == "real":
        return RealLLMClient(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    return MockLLMClient()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.state.settings = settings
    app.state.repository = TicketRepository()
    app.state.service = TriageService(app.state.repository, build_llm_client(settings))

    app.include_router(router)
    return app


app = create_app()

"""Ponto de entrada da aplicação FastAPI."""

from __future__ import annotations

from fastapi import FastAPI

from app.api import router
from app.config import Settings, get_settings
from app.llm.base import LLMClient
from app.llm.mock import MockLLMClient
from app.llm.openai_client import RealLLMClient
from app.service import TriageService
from app.storage import TicketRepository, TicketRepositoryProtocol


def build_llm_client(settings: Settings) -> LLMClient:
    """Fábrica da camada LLM.

    - "mock": MockLLMClient em processo (sem rede).
    - "real": RealLLMClient — HTTP compatível com OpenAI, apontando para
      LLM_BASE_URL (por padrão o container `llm-mock` do compose; troque
      para https://api.openai.com/v1 + LLM_API_KEY para um provedor real).
      Em falha de conexão, o serviço cai no fallback de regras.
    """
    if settings.llm_mode == "real":
        return RealLLMClient(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    return MockLLMClient()


def build_repository(settings: Settings) -> TicketRepositoryProtocol:
    """Fábrica do repositório: "memory" (padrão) ou "redis"."""
    if settings.storage_backend == "redis":
        from app.redis_storage import RedisTicketRepository

        return RedisTicketRepository(redis_url=settings.redis_url)
    return TicketRepository()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, version="0.2.0")

    app.state.settings = settings
    app.state.repository = build_repository(settings)
    app.state.service = TriageService(app.state.repository, build_llm_client(settings))

    app.include_router(router)
    return app


app = create_app()

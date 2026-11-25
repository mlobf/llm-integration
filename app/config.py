"""Configurações da aplicação (via variáveis de ambiente)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    app_name: str = "ticket-triage"
    # Modo do motor de triagem:
    #   "mock" -> MockLLMClient em processo (sem rede)
    #   "real" -> RealLLMClient (HTTP, OpenAI-compatível; aponta para LLM_BASE_URL)
    llm_mode: str = "mock"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = field(default="", repr=False)  # nunca aparecer em logs
    llm_base_url: str = "http://llm-mock:8001/v1"
    llm_timeout_seconds: float = 30.0
    # Backend de armazenamento: "memory" (padrão) ou "redis"
    storage_backend: str = "memory"
    redis_url: str = "redis://redis:6379/0"


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "ticket-triage"),
        llm_mode=os.getenv("LLM_MODE", "mock").lower(),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_base_url=os.getenv("LLM_BASE_URL", "http://llm-mock:8001/v1"),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
        storage_backend=os.getenv("STORAGE", "memory").lower(),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    )

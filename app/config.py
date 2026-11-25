"""Configurações da aplicação (via variáveis de ambiente)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "ticket-triage"
    # Modo do motor de triagem: "mock" usa o MockLLMClient;
    # "real" usaria a integração verdadeira com LLM (ainda não implementada).
    llm_mode: str = "mock"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    llm_timeout_seconds: float = 30.0


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "ticket-triage"),
        llm_mode=os.getenv("LLM_MODE", "mock").lower(),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
    )

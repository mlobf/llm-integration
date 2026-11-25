"""Mock de provedor LLM — servidor HTTP compatível com a API da OpenAI.

Expõe POST /v1/chat/completions e responde no formato OpenAI, onde
`choices[0].message.content` é um JSON com o resultado da triagem
(category, priority, routed_to, confidence, summary).

Internamente reutiliza o motor de regras do próprio projeto para gerar
respostas plausíveis e determinísticas — sem chamar nenhuma LLM real.

Uso (container `llm-mock` no docker-compose):
    uvicorn services.llm_mock:app --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

import json
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.models import Ticket
from app.rules import classify_with_rules

app = FastAPI(title="llm-mock-provider", version="0.1.0")


class ChatCompletionRequest(BaseModel):
    model: str = "mock-model"
    messages: list[dict]
    temperature: float = 0.0


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "provider": "mock"}


def _extract_ticket(messages: list[dict]) -> Ticket:
    """Espera que a última mensagem 'user' contenha o JSON do ticket."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            try:
                return Ticket.model_validate_json(msg["content"])
            except Exception as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Conteúdo da mensagem não é um JSON de Ticket: {exc}",
                ) from exc
    raise HTTPException(status_code=400, detail="Nenhuma mensagem 'user' encontrada")


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> dict:
    ticket = _extract_ticket(request.messages)
    result = classify_with_rules(ticket)
    # O mock é um pouco mais confiante e gera resumo (como uma LLM faria).
    result.confidence = min(round(result.confidence + 0.1, 2), 0.95)
    result.source = "llm"
    desc = " ".join(ticket.description.split())[:120]
    result.summary = f"{ticket.title.strip()}. {desc}".strip()

    return {
        "id": f"chatcmpl-mock-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(result.model_dump(), ensure_ascii=False),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }

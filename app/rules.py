"""Classificação determinística baseada em regras de palavras-chave.

Serve como motor de triagem padrão e como fallback quando a camada LLM
falha ou não está configurada.
"""

from __future__ import annotations

import re

from app.models import Category, Priority, Ticket, TriageResult

# (categoria, equipe destino, palavras-chave)
_CATEGORY_RULES: list[tuple[Category, str, tuple[str, ...]]] = [
    (
        Category.BILLING,
        "billing",
        ("cobrança", "cobranca", "fatura", "invoice", "pagamento", "payment",
         "cartão", "cartao", "reembolso", "refund", "assinatura", "subscription",
         "billing", "charge"),
    ),
    (
        Category.ACCESS,
        "security",
        ("senha", "password", "login", "acesso", "access", "2fa", "mfa",
         "bloqueado", "locked", "autenticação", "autenticacao", "token"),
    ),
    (
        Category.BUG,
        "engineering",
        ("erro", "error", "bug", "falha", "crash", "quebrado", "broken",
         "exception", "traceback", "500", "não funciona", "nao funciona"),
    ),
    (
        Category.FEATURE_REQUEST,
        "product",
        ("feature", "funcionalidade", "sugestão", "sugestao", "gostaria",
         "seria bom", "wishlist", "improvement", "melhoria"),
    ),
    (
        Category.QUESTION,
        "support",
        ("como faço", "como faco", "dúvida", "duvida", "help", "ajuda",
         "como usar", "how to", "how do i", "pergunta", "question"),
    ),
]

_HIGH_PRIORITY = ("urgente", "urgent", "crítico", "critico", "critical",
                  "produção", "producao", "production", "down", "fora do ar",
                  "p1", "severe", "emergência", "emergencia")

_LOW_PRIORITY = ("quando puder", "sem pressa", "low priority", "baixa prioridade",
                 "eventualmente")


def _text_of(ticket: Ticket) -> str:
    parts = [ticket.title, ticket.description, " ".join(ticket.tags)]
    return " ".join(parts).lower()


def _match_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(re.search(re.escape(kw), text) for kw in keywords)


def classify_with_rules(ticket: Ticket) -> TriageResult:
    """Classifica o ticket usando apenas regras determinísticas."""
    text = _text_of(ticket)

    category = Category.OTHER
    team = "support"
    matched = 0
    for cat, dest, keywords in _CATEGORY_RULES:
        hits = sum(1 for kw in keywords if kw in text)
        if hits > matched:
            matched = hits
            category = cat
            team = dest

    priority = Priority.MEDIUM
    if _match_any(text, _HIGH_PRIORITY):
        priority = Priority.HIGH
    if _match_any(text, _LOW_PRIORITY) and priority != Priority.HIGH:
        priority = Priority.LOW
    # Bugs em produção viram críticos.
    if category == Category.BUG and _match_any(text, ("produção", "producao", "production", "down")):
        priority = Priority.CRITICAL

    confidence = min(0.3 + 0.15 * matched, 0.9) if matched else 0.2

    return TriageResult(
        category=category,
        priority=priority,
        routed_to=team,
        confidence=round(confidence, 2),
        summary=None,
        source="rules",
    )

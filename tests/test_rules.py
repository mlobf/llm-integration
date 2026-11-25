import pytest

from app.models import Ticket
from app.rules import classify_with_rules


def make_ticket(title: str, description: str = "", tags: list[str] | None = None) -> Ticket:
    return Ticket(title=title, description=description, tags=tags or [])


def test_billing_ticket():
    result = classify_with_rules(make_ticket("Cobrança duplicada na minha fatura"))
    assert result.category.value == "billing"
    assert result.routed_to == "billing"
    assert result.source == "rules"


def test_access_ticket():
    result = classify_with_rules(make_ticket("Não consigo fazer login, senha resetada não funciona"))
    assert result.category.value == "access"
    assert result.routed_to == "security"


def test_production_bug_is_critical():
    result = classify_with_rules(
        make_ticket("Erro 500 no checkout", "API fora do ar em produção desde as 10h")
    )
    assert result.category.value == "bug"
    assert result.priority.value == "critical"


def test_feature_request():
    result = classify_with_rules(make_ticket("Sugestão: exportar relatórios em PDF"))
    assert result.category.value == "feature_request"
    assert result.routed_to == "product"


def test_question():
    result = classify_with_rules(make_ticket("Como faço para cancelar minha assinatura?"))
    # "assinatura" também é billing; a categoria com mais hits vence.
    assert result.category.value in {"question", "billing"}


def test_unknown_falls_to_other():
    result = classify_with_rules(make_ticket("asdf qwerty", "zzz yyy xxx"))
    assert result.category.value == "other"
    assert result.confidence == 0.2


def test_low_priority_keyword():
    result = classify_with_rules(make_ticket("Dúvida sobre relatório, sem pressa"))
    assert result.priority.value == "low"


def test_confidence_increases_with_matches():
    weak = classify_with_rules(make_ticket("bug"))
    strong = classify_with_rules(make_ticket("bug crítico", "erro exception traceback"))
    assert strong.confidence > weak.confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

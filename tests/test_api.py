import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app(Settings(llm_mode="mock"))
    return TestClient(app)


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm_mode"] == "mock"


def test_create_and_get_ticket(client: TestClient):
    resp = client.post(
        "/tickets",
        json={"title": "Não consigo acessar minha conta", "description": "login falha com 2fa"},
    )
    assert resp.status_code == 201
    ticket = resp.json()
    assert ticket["status"] == "routed"
    assert ticket["triage"]["category"] == "access"

    resp = client.get(f"/tickets/{ticket['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == ticket["id"]


def test_list_tickets(client: TestClient):
    client.post("/tickets", json={"title": "ticket a"})
    client.post("/tickets", json={"title": "ticket b"})
    resp = client.get("/tickets")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_retriage_endpoint(client: TestClient):
    ticket = client.post("/tickets", json={"title": "erro na fatura"}).json()
    resp = client.post(f"/tickets/{ticket['id']}/triage")
    assert resp.status_code == 200
    assert resp.json()["triage"] is not None


def test_get_missing_ticket_404(client: TestClient):
    assert client.get("/tickets/nao-existe").status_code == 404
    assert client.post("/tickets/nao-existe/triage").status_code == 404


def test_delete_ticket(client: TestClient):
    ticket = client.post("/tickets", json={"title": "para deletar"}).json()
    assert client.delete(f"/tickets/{ticket['id']}").status_code == 204
    assert client.get(f"/tickets/{ticket['id']}").status_code == 404


def test_validation_error(client: TestClient):
    assert client.post("/tickets", json={"title": ""}).status_code == 422


def test_real_mode_falls_back_to_rules():
    app = create_app(Settings(llm_mode="real"))
    client = TestClient(app)
    resp = client.post("/tickets", json={"title": "Erro crítico em produção"})
    assert resp.status_code == 201
    triage = resp.json()["triage"]
    # RealLLMClient não implementado → fallback determinístico
    assert triage["source"] == "rules"
    assert triage["category"] == "bug"
    assert client.get("/health").json()["llm_failures"] == 1

# syntax=docker/dockerfile:1
# ---- Estágio de build: instala dependências num venv ----
FROM python:3.14-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /code
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- Estágio runtime: imagem enxuta, usuário não-root ----
FROM python:3.14-slim

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1

WORKDIR /code
COPY app/ ./app/
COPY services/ ./services/

# Usuário não-root (boa prática de segurança)
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000

# /health não depende de LLM nem Redis estarem prontos para responder "ok"
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status==200 else 1)"

# 1 worker por padrão: com STORAGE=memory cada worker teria estado próprio.
# Com STORAGE=redis é seguro aumentar (--workers N).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

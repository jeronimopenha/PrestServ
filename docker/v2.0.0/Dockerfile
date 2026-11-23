# PrestServ V2.0.0 — construa a partir da RAIZ do repositorio.
# Exemplo: docker build -f docker/v2.0.0/Dockerfile -t prestserv:2.0.0 .
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

# Certificados TLS e fontes para relatórios e certificados PDF.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# Dados, backups, segredos e caches sao excluidos pelo .dockerignore na raiz.
COPY . /app

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)" || exit 1

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]

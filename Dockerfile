# ==========================================
# Stage 1: Build stage (Instalar Dependências)
# ==========================================
FROM python:3.12-slim as builder

# Variáveis de ambiente úteis
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instala dependências de sistema pesadas (necessário para compilar certas bibliotecas Python, mas pesadas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Cria o Virtual Environment onde as bibliotecas python serão injetadas
RUN python -m venv /opt/venv

# Adiciona o venv ao PATH! Isto força que o "pip" ou "python" seguintes actuem internamente neste venv.
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# Instala os requerimentos
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ==========================================
# Stage 2: Final runtime image
# ==========================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala apenas as bibliotecas essenciais runtime (ex: libpq5, que é bem mais leve que libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copia o Virtual Environment compilado perfeitamente da stage anterior (builder)
COPY --from=builder /opt/venv /opt/venv

# Informa o Sistema Operacional da imagem para procurar binários primeiramente neste venv
ENV PATH="/opt/venv/bin:$PATH"

# Copia o código do projeto para o container
COPY . .

# Copia o entrypoint script e garante permissões
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

# Executar o entrypoint script.
# Este script vai tratar das migrações e de correr o collectstatic, e depois passa para o daphne
ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "vibing.asgi:application"]

# Single container for the live demo (Hugging Face Docker Space):
# FalkorDB + FastAPI backend + built React frontend, all on port 7860.

# ---- 1. build the React app
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- 2. FalkorDB image + Python backend
FROM falkordb/falkordb-server:latest
COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /usr/local/bin/uv

ENV UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    FALKORDB_HOST=localhost \
    FALKORDB_PORT=6379 \
    PORT=7860

WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --python 3.11

COPY catalog/ /app/catalog/
COPY backend/ /app/backend/
COPY --from=web /web/dist /app/frontend/dist
COPY start.sh /app/start.sh

# Hugging Face runs containers as uid 1000: make the data dir writable for it
RUN chmod +x /app/start.sh \
    && mkdir -p /var/lib/falkordb/data \
    && chown -R 1000:1000 /var/lib/falkordb/data /app

USER 1000
EXPOSE 7860
ENTRYPOINT []
CMD ["/app/start.sh"]

FROM node:24-bookworm-slim AS mcp-build
RUN npm install --global --omit=dev \
    @modelcontextprotocol/server-filesystem@1.0.0 \
    open-meteo-mcp-server@2.5.2

FROM python:3.13-slim-bookworm AS python-build
WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim-bookworm
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_USE_INSTALLED=1 \
    PORT=8080
COPY --from=python-build /opt/venv /opt/venv
COPY --from=mcp-build /usr/local/bin/node /usr/local/bin/node
COPY --from=mcp-build /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js /usr/local/bin/mcp-server-filesystem \
    && ln -s /usr/local/lib/node_modules/open-meteo-mcp-server/dist/index.js /usr/local/bin/open-meteo-mcp-server \
    && useradd --create-home --uid 10001 appuser \
    && mkdir /app && chown appuser:appuser /app
WORKDIR /app
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser sample_files/ sample_files/
USER appuser
EXPOSE 8080
CMD ["python", "main.py"]

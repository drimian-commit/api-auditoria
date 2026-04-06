# Stage 1: Builder
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Stage 2: Runtime
FROM python:3.12-slim-bookworm

RUN groupadd --gid 999 appgroup && \
    useradd --uid 999 --gid appgroup --create-home appuser

COPY --from=builder /app /app

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8710"]

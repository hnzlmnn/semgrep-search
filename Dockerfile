FROM ghcr.io/astral-sh/uv:python3.12-alpine

RUN apk update && apk add --no-cache \
    cargo \
    curl \
    gcc \
    musl-dev \
    rust

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

WORKDIR /app
COPY . .

RUN uv sync --locked --no-dev
RUN uv pip install -e .

ENTRYPOINT ["sgs"]
CMD ["--help"]

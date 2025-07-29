FROM python:3.12-alpine

RUN apk update && apk add --no-cache \
    cargo \
    curl \
    gcc \
    musl-dev \
    rust

ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app
COPY . .

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

RUN poetry config virtualenvs.create false

ENTRYPOINT ["poetry", "run", "sgs"]
CMD ["--help"]

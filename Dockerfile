FROM python:alpine

RUN apk add curl

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /build

COPY poetry.lock pyproject.toml ./

RUN /root/.local/bin/poetry config virtualenvs.create false \
  && /root/.local/bin/poetry install --no-interaction --no-ansi

COPY . ./

WORKDIR /app

ENTRYPOINT ["/root/.local/bin/poetry", "run", "sgs"]
CMD ["--help"]
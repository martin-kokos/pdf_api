# Builder stage
FROM python:3.11-slim as builder

ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_NO_INTERACTION=1
ENV PATH="$POETRY_HOME/bin:$PATH"

# install poetry
RUN apt update \
    && apt-get install -y --no-install-recommends curl \
        && curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /pdf_api
COPY . /pdf_api

RUN poetry install --no-root --no-ansi --without dev

# Runner stage
FROM python:3.11-slim as runner

# psycopg rdeps
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/pdf_api/.venv/bin:$PATH"

WORKDIR /pdf_api
COPY --from=builder /pdf_api .

CMD ["uvicorn", "pdf_api.app:app", "--host", "0.0.0.0", "--port", "80"]

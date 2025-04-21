FROM python:3.12

RUN apt-get update && apt-get install -y curl build-essential libpq-dev

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

RUN apt-get update && apt-get install -y redis-server && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-root

COPY . .

CMD ["sh", "-c", "redis-server --daemonize yes && alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]

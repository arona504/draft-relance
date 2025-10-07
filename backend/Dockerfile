FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY casbin /app/casbin

RUN pip install --upgrade pip && pip wheel --no-deps --wheel-dir /wheels .

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN python -m venv /opt/venv

COPY --from=builder /wheels /wheels
RUN /opt/venv/bin/pip install --upgrade pip && /opt/venv/bin/pip install --no-cache-dir /wheels/* && rm -rf /wheels

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY casbin /app/casbin

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

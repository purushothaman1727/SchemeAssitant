FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    CHROMA_PATH=/app/data/chroma EMBEDDING_CACHE_DIR=/app/data/models

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY data ./data

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data/chroma /app/data/models \
    && chown -R appuser /app/data
USER appuser

WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python -m app.scripts.seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers"]

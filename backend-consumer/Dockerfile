FROM python:3.11-slim-bookworm

WORKDIR /app
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app \
    && chown appuser:appuser /app

COPY --chown=appuser:appuser shared /app/shared
COPY --chown=appuser:appuser backend-consumer /app/backend-consumer

RUN pip install --no-cache-dir -r /app/backend-consumer/requirements.txt \
    && pip install --no-cache-dir -r /app/shared/requirements.txt

ENV PYTHONPATH=/app/shared:/app/backend-consumer/src \
    PYTHONUNBUFFERED=1

USER appuser
EXPOSE 8080
CMD ["python", "-m", "backend_consumer"]

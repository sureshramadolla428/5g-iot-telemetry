FROM python:3.11-slim-bookworm

# Direct-mode only. 5G bind to uesimtunN must run on the Linux host, not here.
WORKDIR /app
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser shared /app/shared
COPY --chown=appuser:appuser ue-simulator /app/ue-simulator
COPY --chown=appuser:appuser config /app/config

RUN pip install --no-cache-dir -r /app/ue-simulator/requirements.txt \
    && pip install --no-cache-dir -r /app/shared/requirements.txt

ENV PYTHONPATH=/app/shared:/app/ue-simulator/src \
    BIND_MODE=direct \
    DEVICE_MAP_PATH=/app/config/devices.yaml

USER appuser
CMD ["python", "-m", "ue_simulator"]

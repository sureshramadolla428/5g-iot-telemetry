# Ubuntu-oriented helpers. On Windows, use Git Bash or run the listed docker commands directly.
# Operator bash trees (scripts/, private/) live in the private companion
# repo 5g-iot-telemetry-scripts and are gitignored here.
COMPOSE := docker compose -p 5g-iot-telemetry --env-file .env -f docker-compose.yml
PYTHON  := .venv/bin/python

.PHONY: help setup start stop logs test lint sim-direct sim-5g extras-up extras-down

help:
	@echo "setup          Print public bootstrap steps (venv + .env)"
	@echo "start          Start THIS compose project only"
	@echo "stop           Stop THIS compose project only"
	@echo "logs           Follow compose logs for this project"
	@echo "test           Run unit tests in .venv"
	@echo "lint           ruff check"
	@echo "sim-direct     Host UE simulator with BIND_MODE=direct"
	@echo "sim-5g         Host UE simulator with BIND_MODE=5g (requires devices.yaml)"
	@echo "extras-up      Start Kafka+RabbitMQ profile"

setup:
	@echo "cp .env.example .env  # then edit passwords"
	@echo "python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt"
	@echo "Operator setup.sh is in private repo 5g-iot-telemetry-scripts"

start:
	$(COMPOSE) up --build -d

stop:
	$(COMPOSE) stop

logs:
	$(COMPOSE) logs -f --tail=100

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check shared ue-simulator/src backend-consumer/src tests

sim-direct:
	BIND_MODE=direct MQTT_HOST=127.0.0.1 MQTT_PORT=$${MQTT_HOST_PORT:-18830} \
	  $(PYTHON) -m ue_simulator

sim-5g:
	BIND_MODE=5g $(PYTHON) -m ue_simulator

extras-up:
	$(COMPOSE) --profile extras up -d kafka rabbitmq

extras-down:
	$(COMPOSE) --profile extras stop kafka rabbitmq

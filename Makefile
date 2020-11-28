SHELL := /bin/bash # Use bash syntax

install:
	pip install --upgrade pip && \
	pip install poetry && \
	poetry install


test:
	pytest --cov=digirent tests/

build:
	docker-compose -f docker-compose.yml build


build-api-prod:
	docker build -t ghcr.io/ariento89/digirent-api:prod .

build-nginx-prod:
	docker build -t ghcr.io/ariento89/digirent-nginx:prod .

build-prod: build-api-prod build-nginx-prod

serve:
	docker-compose -f docker-compose.yml up --build -d

serve-prod:
	docker-compose -f docker-compose.prod.yml up --build -d

migrate:
	docker-compose run digirent alembic upgrade head

migrate-prod:
	docker-compose -f docker-compose.prod.yml run digirent alembic upgrade head

bash:
	docker-compose -f docker-compose.yml run digirent bash

bash-prod:
	docker-compose -f docker-compose.prod.yml run digirent bash

logs:
	docker-compose logs -f

logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f

api-logs:
	docker-compose logs -f digirent

api-logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f digirent

rent-worker-logs:
	docker-compose logs -f digirent-rent-worker

rent-worker-logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f digirent-rent-worker

subscription-worker-logs:
	docker-compose logs -f digirent-subscription-worker

subscription-worker-logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f digirent-subscription-worker

redis-logs:
	docker-compose logs -f digirent-redis

redis-logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f digirent-redis

beat-logs:
	docker-compose logs -f digirent-beat

beat-logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f digirent-beat

reset:
	docker-compose rm -fsv

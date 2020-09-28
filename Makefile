SHELL := /bin/bash # Use bash syntax

install:
	pip install --upgrade pip && \
	pip install poetry && \
	poetry install


test:
	pytest --cov=digirent tests/

build:
	docker-compose -f docker-compose.yml build

serve:
	docker-compose -f docker-compose.yml up --build -d

migrate:
	docker-compose run digirent alembic upgrade head

bash:
	docker-compose run digirent bash

logs:
	docker-compose logs -f digirent

reset:
	docker-compose rm -fsv

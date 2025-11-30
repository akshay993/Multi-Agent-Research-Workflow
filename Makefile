.PHONY: help format lint type-check check build up down clean

help:
	@echo "Available commands:"
	@echo "  make format     - Format code with black and isort"
	@echo "  make lint       - Run flake8 linter"
	@echo "  make type-check - Run mypy type checker"
	@echo "  make check      - Run format, lint, and type-check"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start services"
	@echo "  make down       - Stop services"
	@echo "  make clean      - Remove containers and volumes"

format:
	docker-compose run --rm app black .
	docker-compose run --rm app isort .

lint:
	docker-compose run --rm app flake8 .

type-check:
	docker-compose run --rm app mypy .

check: format lint type-check

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

clean:
	docker-compose down -v

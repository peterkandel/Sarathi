SHELL := /bin/zsh

.PHONY: up down logs lint-python lint-web format-python format-web

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=100

lint-python:
	python -m compileall apps services packages

lint-web:
	pnpm --dir apps/mobile lint

format-python:
	python -m compileall apps services packages

format-web:
	pnpm --dir apps/mobile format

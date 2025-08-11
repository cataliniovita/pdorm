SHELL := /bin/bash

.PHONY: build up down clean test

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down -v

clean: down
	rm -f report.md vuln-report.json || true

test:
	docker compose up --build attacker



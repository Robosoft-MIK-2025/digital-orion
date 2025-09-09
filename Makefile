SHELL := /bin/bash

.PHONY: help build up shell stop clean docs

help:
	@echo "Targets: build, up, shell, stop, clean, docs"

build:
	docker build -t digital-oreon:humble -f docker/Dockerfile .

up:
	cd docker && docker compose up -d terminal

shell:
	cd docker && docker compose exec terminal bash

stop:
	cd docker && docker compose down || true

clean:
	rm -rf docs/_build || true

docs:
	python3 -m venv .venv && source .venv/bin/activate && \
		pip install -r docs/requirements-docs.txt && \
		sphinx-build -b html docs docs/_build/html



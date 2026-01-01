.PHONY: setup lock test run env
SHELL := /usr/bin/env fish

setup:
	uv sync --all-extras

lock:
	uv lock

test:
	uv run pytest

run:
	uv run python main.py

env:
	@test -f .env; or cp .env.example .env

.PHONY: run run-demo compile lint format test check docker-up

run:
	python -m src.pipeline

run-demo:
	python -m src.pipeline --demo

compile:
	python -m compileall src

lint:
	ruff check src tests
	black --check src tests

format:
	black src tests
	ruff check --fix src tests

test:
	pytest -q

check: compile lint test

docker-up:
	docker compose up --build

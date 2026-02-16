.PHONY: run run-demo compile lint format test check docker-up verify-postgres \
	postgres-up postgres-down ingest-raw dbt-run dbt-test pipeline-ml run-all

run:
	python -m src.pipeline --demo

run-demo:
	python -m src.pipeline --demo

compile:
	python -m compileall src

lint:
	ruff check src tests scripts
	black --check src tests scripts

format:
	black src tests scripts
	ruff check --fix src tests scripts

test:
	pytest -q

check: compile lint test

postgres-up:
	docker compose up -d postgres

postgres-down:
	docker compose down -v

ingest-raw:
	python scripts/ingest_raw_postgres.py

dbt-run:
	cd dbt_oulad && dbt run

dbt-test:
	cd dbt_oulad && dbt test

pipeline-ml:
	python -m src.pipeline

run-all: postgres-up ingest-raw pipeline-ml dbt-run dbt-test

verify-postgres:
	docker compose exec -T postgres psql -U oulad -d oulad_analytics -c "\\dt raw.*"
	docker compose exec -T postgres psql -U oulad -d oulad_analytics -c "\\dt ml.*"
	docker compose exec -T postgres psql -U oulad -d oulad_analytics -c "\\dt mart.*"
	docker compose exec -T postgres psql -U oulad -d oulad_analytics -c "select min(week), max(week), count(distinct week) from mart.mart_student_risk_weekly;"
	docker compose exec -T postgres psql -U oulad -d oulad_analytics -c "select min(week), max(week), count(distinct week) from mart.mart_course_summary_weekly;"
	docker compose exec -T postgres psql -U oulad -d oulad_analytics -c "select count(*) as total_rows, count(risk_score) as non_null_risk_score from mart.mart_student_risk_weekly;"

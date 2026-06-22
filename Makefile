.PHONY: help install deploy test docs clean lint format generate-data

help:
	@echo "ConsolidAR - available targets:"
	@echo ""
	@echo "  install         Install Python dependencies via Poetry"
	@echo "  generate-data   Generate synthetic data for 5 entities x 24 months"
	@echo "  deploy          Deploy DDL + dbt models to Snowflake"
	@echo "  test            Run pytest + dbt tests"
	@echo "  docs            Generate and serve dbt docs locally"
	@echo "  lint            Run ruff + mypy"
	@echo "  format          Run ruff format"
	@echo "  clean           Remove generated artifacts (target/, dbt_packages/, __pycache__)"
	@echo ""

install:
	poetry install

generate-data:
	@echo "TODO (Commit 3): implement data generation pipeline"
	# poetry run python data_generation/generate_synthetic_data.py
	# poetry run python data_generation/fx_rates_downloader.py

deploy:
	@echo "TODO (Phase 1 - Trial Day 1): implement Snowflake deployment"
	# poetry run python snowflake/deploy_ddl.py
	# cd dbt && poetry run dbt build --target prod

test:
	@echo "TODO: run pytest and dbt tests"
	# poetry run pytest
	# cd dbt && poetry run dbt test

docs:
	@echo "TODO: generate dbt docs"
	# cd dbt && poetry run dbt docs generate && poetry run dbt docs serve

lint:
	poetry run ruff check .
	poetry run mypy data_generation snowpark

format:
	poetry run ruff format .

clean:
	rm -rf dbt/target dbt/dbt_packages dbt/logs
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

.PHONY: help install install-dev lock deploy test docs clean lint format generate-data

help:
	@echo "ConsolidAR - available targets:"
	@echo ""
	@echo "  install         Install runtime dependencies (uses requirements-lock.txt)"
	@echo "  install-dev     Install runtime + dev dependencies (pytest, ruff, mypy)"
	@echo "  lock            Regenerate requirements-lock.txt from current environment"
	@echo "  generate-data   Generate synthetic data for 5 entities x 24 months"
	@echo "  deploy          Deploy DDL + dbt models to Snowflake"
	@echo "  test            Run pytest + dbt tests"
	@echo "  docs            Generate and serve dbt docs locally"
	@echo "  lint            Run ruff + mypy"
	@echo "  format          Run ruff format"
	@echo "  clean           Remove generated artifacts"
	@echo ""
	@echo "Note: all targets assume the project's virtualenv is active."
	@echo "      Activate with: source .venv/bin/activate"
	@echo ""

install:
	pip install -r requirements-lock.txt

install-dev:
	pip install -r requirements-dev.txt

lock:
	pip install -r requirements.txt --upgrade
	pip freeze > requirements-lock.txt
	@echo "requirements-lock.txt regenerated."

generate-data:
	@echo "TODO (next commit): implement data generation pipeline"
	# python data_generation/generate_synthetic_data.py
	# python data_generation/fx_rates_downloader.py

deploy:
	@echo "TODO (Phase 1 - Trial Day 1): implement Snowflake deployment"
	# python snowflake/deploy_ddl.py
	# cd dbt && dbt build --target prod

test:
	@echo "TODO: run pytest and dbt tests"
	# pytest
	# cd dbt && dbt test

docs:
	@echo "TODO: generate dbt docs"
	# cd dbt && dbt docs generate && dbt docs serve

lint:
	ruff check .
	@if find data_generation snowpark -name "*.py" -type f | grep -q .; then \
		mypy; \
	else \
		echo "mypy: skipped (no .py files yet in data_generation/snowpark)"; \
	fi

format:
	ruff format .

clean:
	rm -rf dbt/target dbt/dbt_packages dbt/logs
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

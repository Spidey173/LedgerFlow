.PHONY: all run test etl load api docker clean help

all: run

run:
	bash run_all.sh

test:
	pytest -v

etl:
	python3 scripts/run_pipeline.py

load:
	python3 scripts/load_postgres.py

api:
	uvicorn scripts.api:app --host 0.0.0.0 --port 8000 --reload

docker:
	docker-compose up --build -d

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

help:
	@echo "LedgerFlow: Modern Banking Data Platform - Available Commands:"
	@echo "  make run     - Run unit tests and full 10-dataset ETL pipeline (one-command run)"
	@echo "  make test    - Run 41 validator test cases with pytest"
	@echo "  make etl     - Run the master ETL pipeline across all 10 datasets"
	@echo "  make load    - Bulk load curated data into PostgreSQL data warehouse"
	@echo "  make api     - Start FastAPI REST service on http://localhost:8000"
	@echo "  make docker  - Build and run PostgreSQL + API in Docker containers"
	@echo "  make clean   - Clean cache directories"

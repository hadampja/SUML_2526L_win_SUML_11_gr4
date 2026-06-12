.PHONY: help install install-dev kedro-eda kedro-prep kedro-model kedro-all run-api run-ui test lint pylint ruff finch-up finch-down clean

PY ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTHON := $(VENV)/bin/python

help: ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "} {printf "  %-15s %s\n", $$1, $$2}'

$(VENV)/bin/activate: requirements.txt
	$(PY) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@touch $(VENV)/bin/activate

install: $(VENV)/bin/activate ## Install runtime dependencies into .venv
install-dev: install ## Install runtime + dev dependencies (pylint, pytest, ruff)
	$(PIP) install -r requirements-dev.txt

kedro-eda: install ## Run the EDA Kedro pipeline
	$(VENV)/bin/kedro run --pipeline=eda
kedro-prep: install ## Run the preprocessing Kedro pipeline
	$(VENV)/bin/kedro run --pipeline=preprocessing
kedro-model: install ## Run the modeling Kedro pipeline (builds recommendations)
	$(VENV)/bin/kedro run --pipeline=modeling
kedro-all: install ## Run the full default Kedro pipeline
	$(VENV)/bin/kedro run

run-api: install ## Start the FastAPI service on http://127.0.0.1:8000
	$(VENV)/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
run-ui: install ## Start the Streamlit UI on http://localhost:8501
	API_URL=http://127.0.0.1:8000 $(VENV)/bin/streamlit run frontend/app.py

test: install-dev ## Run the test suite
	$(PYTHON) -m pytest -q
ruff: install-dev ## Run ruff lint
	$(VENV)/bin/ruff check .
pylint: install-dev ## Run pylint and require score >= 8.0
	$(VENV)/bin/pylint --rcfile=.pylintrc --fail-under=8.0 src/ai_project_s28551 app
lint: ruff pylint ## Run all linters

finch-up: ## Build and start backend + frontend with Finch (or Docker)
	finch compose up --build -d
finch-down: ## Stop and remove the Finch containers
	finch compose down

clean: ## Remove caches and the virtual environment
	rm -rf $(VENV) .pytest_cache .ruff_cache build dist *.egg-info
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +

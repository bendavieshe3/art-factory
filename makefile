# Makefile for Art Factory project

# Variables
VENV_DIR := venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
PRE_COMMIT := $(VENV_DIR)/bin/pre-commit

# Create virtual environment
$(VENV_DIR):
	python3.11 -m venv $(VENV_DIR)

# Install Python dependencies
install: $(VENV_DIR)
	$(PIP) install -r requirements.txt
	npm install

# Install pre-commit hooks
pre-commit-install: $(VENV_DIR)
	$(PIP) install pre-commit
	$(PRE_COMMIT) install

# Run pre-commit hooks
pre-commit-run: $(VENV_DIR)
	$(PRE_COMMIT) run --all-files

# Lint Python and JavaScript code
lint: $(VENV_DIR)
	$(VENV_DIR)/bin/pylint my_project/
	npx eslint src/

# Run tests
test: $(VENV_DIR)
	tox

# Clean the virtual environment
clean:
	rm -rf $(VENV_DIR)

# Full setup
setup: clean install pre-commit-install

# Run Django server
run-server: $(VENV_DIR)
	$(PYTHON) manage.py runserver

.PHONY: install pre-commit-install pre-commit-run lint test clean setup run-server

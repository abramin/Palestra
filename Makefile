VENV ?= env
PYTHON_SYSTEM ?= python
VENV_PYTHON := $(VENV)/bin/python

PYTHON := $(PYTHON_SYSTEM)
ifneq (,$(wildcard $(VENV_PYTHON)))
PYTHON := $(VENV_PYTHON)
endif

PIP := $(PYTHON) -m pip

.PHONY: help venv setup test test-one lint clean

help:
	@echo "Targets:"
	@echo "  make setup  - install dependencies"
	@echo "  make test   - run tests"
	@echo "  make test-one TEST_FILE=tests/test_file.py [TEST_NAME=TestName] [TEST_CASE=test_case]  - run one test"

venv:
	$(PYTHON_SYSTEM) -m venv $(VENV)

setup: venv
	$(VENV_PYTHON) -m pip install -r requirements.txt

test: setup
	$(VENV_PYTHON) -m pytest

test-one: setup
ifndef TEST_FILE
	$(error TEST_FILE is required, e.g. make test-one TEST_FILE=tests/test_file.py)
endif
	$(VENV_PYTHON) -m pytest $(TEST_FILE)$(if $(TEST_NAME),::$(TEST_NAME))$(if $(TEST_CASE),::$(TEST_CASE))

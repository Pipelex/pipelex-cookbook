# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

ifeq ($(wildcard .env),.env)
include .env
export
endif
VIRTUAL_ENV := $(CURDIR)/.venv
LOCAL_PYTHON := $(VIRTUAL_ENV)/bin/python3.11
PROJECT_NAME := $(shell grep '^name = ' pyproject.toml | sed -E 's/name = "(.*)"/\1/')

LOCAL_MYPY := $(VIRTUAL_ENV)/bin/mypy
LOCAL_PYTEST := $(VIRTUAL_ENV)/bin/pytest
LOCAL_PYRIGHT := $(VIRTUAL_ENV)/bin/pyright
LOCAL_RUFF := $(VIRTUAL_ENV)/bin/ruff

define PRINT_TITLE
    $(eval PADDED_PROJECT_NAME := $(shell printf '%-15s' "[$(PROJECT_NAME)] " | sed 's/ /=/g'))
    $(eval PADDED_TARGET_NAME := $(shell printf '%-15s' "($@) " | sed 's/ /=/g'))
    $(if $(1),\
		$(eval TITLE := $(shell printf '%s' "=== $(PADDED_PROJECT_NAME) $(PADDED_TARGET_NAME)" | sed 's/[[:space:]]/ /g')$(shell echo " $(1) " | sed 's/[[:space:]]/ /g')),\
		$(eval TITLE := $(shell printf '%s' "=== $(PADDED_PROJECT_NAME) $(PADDED_TARGET_NAME)" | sed 's/[[:space:]]/ /g'))\
	)
	$(eval PADDED_TITLE := $(shell printf '%-126s' "$(TITLE)" | sed 's/ /=/g'))
	@echo ""
	@echo "$(PADDED_TITLE)"
endef

define HELP
Manage $(PROJECT_NAME) located in $(CURDIR).
Usage:

make env                      - Create python virtual env
make lock                     - Refresh poetry.lock without updating anything
make install                  - Create local virtualenv & install all dependencies
make update                   - Upgrade dependencies via poetry

make format                   - format with ruff format
make lint                     - lint with ruff check
make pyright                  - Check types with pyright
make mypy                     - Check types with mypy

make cleanenv                 - Remove virtual env and lock files
make cleanderived             - Remove extraneous compiled files, caches, logs, etc.
make cleanlibraries           - Remove pipelex_libraries
make cleanall                 - Remove all -> cleanenv + cleanderived + cleanlibraries
make reinitlibraries          - Remove pipelex_libraries and init libraries again

make merge-check-ruff-lint    - Run ruff merge check without updating files
make merge-check-ruff-format  - Run ruff merge check without updating files
make merge-check-mypy         - Run mypy merge check without updating files
make merge-check-pyright	  - Run pyright merge check without updating files

make rl                       - Shorthand -> reinitlibraries
make run-setup                - Run the setup sequence
make s                        - Shorthand -> run-setup
make init                     - Run pipelex init
make runtests		          - Run tests for github actions (exit on first failure) (no inference)
make test                     - Run unit tests (no inference)
make tn                       - Shorthand -> test
make test-with-prints         - Run tests with prints (no inference)
make t                        - Shorthand -> test-with-prints
make test-inference           - Run unit tests only for inference (with prints)
make ti                       - Shorthand -> test-inference
make test-imgg                - Run unit tests only for imgg (with prints)

make check                    - Shorthand -> format lint mypy
make c                        - Shorthand -> check
make cc                       - Shorthand -> cleanderived check
make li                       - Shorthand -> lock install
make check-unused-imports     - Check for unused imports without fixing
make fix-unused-imports       - Fix unused imports with ruff
make reuse                    - Add license headers and check compliance
make reuse-check              - Check license headers without annotating

endef
export HELP

.PHONY: all help env lock install update format lint pyright mypy cleanderived cleanenv run-setup s runtests test test-with-prints test-inference t ti test-imgg check cc li merge-check-ruff-lint merge-check-ruff-format merge-check-mypy check-unused-imports fix-unused-imports test-name bump-version reuse reuse-check

all help:
	@echo "$$HELP"


##########################################################################################
### SETUP
##########################################################################################

env:
	$(call PRINT_TITLE,"Creating virtual environment")
	@if [ ! -d $(VIRTUAL_ENV) ]; then \
		echo "Creating Python virtual env in \`${VIRTUAL_ENV}\`"; \
		python3.11 -m venv $(VIRTUAL_ENV); \
		. $(VIRTUAL_ENV)/bin/activate && \
		echo "Created Python virtual env in \`${VIRTUAL_ENV}\`"; \
	else \
		echo "Python virtual env already exists in \`${VIRTUAL_ENV}\`"; \
	fi

init: env
	$(call PRINT_TITLE,"Running `pipelex init`")
	pipelex init

install: env
	$(call PRINT_TITLE,"Installing dependencies")
	@. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_PYTHON) -m pip install --upgrade pip setuptools wheel && \
	$(LOCAL_PYTHON) -m pip install "poetry>=2.0.0,<2.1.0" && \
	$(LOCAL_PYTHON) -m poetry install && \
	pipelex init && \
	echo "Installed Pipelex coobook dependencies in ${VIRTUAL_ENV} and initialized Pipelex libraries";

lock: env
	$(call PRINT_TITLE,"Resolving dependencies without update")
	@. $(VIRTUAL_ENV)/bin/activate && \
	poetry lock && \
	echo poetry lock without update;

update: env
	$(call PRINT_TITLE,"Updating all dependencies")
	@. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_PYTHON) -m pip install --upgrade pip setuptools wheel && \
	poetry update && \
	echo "Updated dependencies in ${VIRTUAL_ENV}";

run-setup: env
	$(call PRINT_TITLE,"Running setup sequence")
	pipelex run-setup

##############################################################################################
############################      Cleaning                        ############################
##############################################################################################

cleanderived:
	$(call PRINT_TITLE,"Erasing derived files and directories")
	@find . -name '.coverage' -delete && \
	find . -wholename '**/*.pyc' -delete && \
	find . -type d -wholename '__pycache__' -exec rm -rf {} + && \
	find . -type d -wholename './.cache' -exec rm -rf {} + && \
	find . -type d -wholename './.mypy_cache' -exec rm -rf {} + && \
	find . -type d -wholename './.ruff_cache' -exec rm -rf {} + && \
	find . -type d -wholename '.pytest_cache' -exec rm -rf {} + && \
	find . -type d -wholename '**/.pytest_cache' -exec rm -rf {} + && \
	find . -type d -wholename './logs/*.log' -exec rm -rf {} + && \
	find . -type d -wholename './.reports/*' -exec rm -rf {} + && \
	echo "Cleaned up derived files and directories";

cleanenv:
	$(call PRINT_TITLE,"Erasing virtual environment")
	find . -name '.Pipfile.lock' -delete && \
	find . -type d -wholename './.venv' -exec rm -rf {} + && \
	echo "Cleaned up virtual env and dependency lock files";

cleanbaselibrary:
	$(call PRINT_TITLE,"Erasing derived files and directories")
	@find . -type d -wholename './pipelex_libraries/pipelines/base_library' -exec rm -rf {} + && \
	echo "Cleaned up pipelex base library";

reinitbaselibrary: cleanbaselibrary init
	@echo "Reinitialized pipelex base library";

rl: reinitbaselibrary
	@echo "> done: rl = reinitlibraries"

cleanall: cleanderived cleanenv cleanlibraries
	@echo "Cleaned up all derived files and directories";

##########################################################################################
### TESTING
##########################################################################################

runtests: env
	$(call PRINT_TITLE,"Unit testing for github actions")
	@echo "• Running unit tests (excluding inference, and gha_disabled)"
	$(LOCAL_PYTEST) --exitfirst --quiet -m "not inference and not gha_disabled" || [ $$? = 5 ]

run-all-tests: env
	$(call PRINT_TITLE,"Running all unit tests")
	@echo "• Running all unit tests"
	$(LOCAL_PYTEST) --exitfirst --quiet

run-manual-trigger-gha-tests: env
	$(call PRINT_TITLE,"Running GHA tests")
	@echo "• Running GHA unit tests for inference, llm, and not gha_disabled"
	$(LOCAL_PYTEST) --exitfirst --quiet -m "not gha_disabled and (inference or llm)" || [ $$? = 5 ]

run-gha_disabled-tests: env
	$(call PRINT_TITLE,"Running GHA disabled tests")
	@echo "• Running GHA disabled unit tests"
	$(LOCAL_PYTEST) --exitfirst --quiet -m "gha_disabled" || [ $$? = 5 ]

test: env
	$(call PRINT_TITLE,"Unit testing without prints but displaying logs via pytest for WARNING level and above")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(LOCAL_PYTEST) -o log_cli=true -o log_level=WARNING -k "$(TEST)" $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	else \
		$(LOCAL_PYTEST) -o log_cli=true -o log_level=WARNING $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	fi

tn: test
	@echo "> done: tn = test"

test-with-prints: env
	$(call PRINT_TITLE,"Unit testing with prints and our rich logs")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(LOCAL_PYTEST) -s -k "$(TEST)" $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	else \
		$(LOCAL_PYTEST) -s $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	fi

t: test-with-prints
	@echo "> done: t = test-with-prints"

test-inference: env
	$(call PRINT_TITLE,"Unit testing")
	@if [ -n "$(TEST)" ]; then \
		$(LOCAL_PYTEST) --exitfirst -m "inference and not imgg" -s -k "$(TEST)" $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	else \
		$(LOCAL_PYTEST) --exitfirst -m "inference and not imgg" -s $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	fi

ti: test-inference
	@echo "> done: ti = test-inference"

test-imgg: env
	$(call PRINT_TITLE,"Unit testing")
	@if [ -n "$(TEST)" ]; then \
		$(LOCAL_PYTEST) --exitfirst -m "imgg" -s -k "$(TEST)" $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	else \
		$(LOCAL_PYTEST) --exitfirst -m "imgg" -s $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	fi

############################################################################################
############################               Linting              ############################
############################################################################################

format: env
	$(call PRINT_TITLE,"Formatting with ruff")
	@$(LOCAL_RUFF) format .

lint: env
	$(call PRINT_TITLE,"Linting with ruff")
	@$(LOCAL_RUFF) check . --fix

pyright: env
	$(call PRINT_TITLE,"Typechecking with pyright")
	@$(LOCAL_PYRIGHT) --pythonpath $(LOCAL_PYTHON)

mypy: env
	$(call PRINT_TITLE,"Typechecking with mypy")
	@$(LOCAL_PYTHON) $(LOCAL_MYPY)


##########################################################################################
### MERGE CHECKS
##########################################################################################

merge-check-ruff-format: env
	$(call PRINT_TITLE,"Formatting with ruff")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_RUFF) format --check -v .

merge-check-ruff-lint: env check-unused-imports
	$(call PRINT_TITLE,"Linting with ruff without fixing files")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_RUFF) check -v .

merge-check-pyright: env
	$(call PRINT_TITLE,"Typechecking with pyright")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_PYRIGHT) -p pyproject.toml

merge-check-mypy: env
	$(call PRINT_TITLE,"Typechecking with mypy")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_PYTHON) $(LOCAL_MYPY) --version && \
	$(LOCAL_PYTHON) $(LOCAL_MYPY) --config-file pyproject.toml

##########################################################################################
### SHORTHANDS
##########################################################################################

check-unused-imports: env
	$(call PRINT_TITLE,"Checking for unused imports without fixing")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_RUFF) check --select=F401 --no-fix .

c: init format lint pyright mypy
	@echo "> done: c = check"

cc: init cleanderived c
	@echo "> done: cc = cleanderived check"

check: init cleanderived check-unused-imports reuse-check c
	@echo "> done: check"

s: init run-setup
	@echo "> done: s = run-setup"

li: lock install
	@echo "> done: lock install"

fix-unused-imports: env
	$(call PRINT_TITLE,"Fixing unused imports")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_RUFF) check --select=F401 --fix -v .

CURRENT_VERSION := $(shell grep '^version = ' pyproject.toml | sed -E 's/version = "(.*)"/\1/')
NEXT_VERSION := $(shell echo $(CURRENT_VERSION) | awk -F. '{$$NF = $$NF + 1;} 1' | sed 's/ /./g')

bump-version: env
	$(call PRINT_TITLE,"Bumping version from $(CURRENT_VERSION) to $(NEXT_VERSION)")
	@. $(VIRTUAL_ENV)/bin/activate && poetry version $(NEXT_VERSION)
	@echo "Version bumped to $(NEXT_VERSION)"

##########################################################################################
### LICENSE MANAGEMENT
##########################################################################################

reuse: env
	$(call PRINT_TITLE,"Running reuse annotate and lint to check license headers")
	@. $(VIRTUAL_ENV)/bin/activate && \
	find cookbook tests pipelex_libraries -type f \( -name "*.py" -o -name "*.toml" -o -name "*.env.example" \) -print0 | xargs -0 \
		reuse annotate --license Elastic-2.0 --copyright-prefix spdx-symbol --year 2025 --copyright "Evotis S.A.S." --template cookbook --skip-unrecognised --skip-existing >/dev/null && \
		reuse lint --quiet || { \
		echo '⚠  REUSE check failed – full report below:' ; \
		reuse lint ; \
		exit $$? ; \
	}
	@echo "Done running reuse annotate and lint to check license headers"

reuse-check: env
	$(call PRINT_TITLE,"Checking license headers without annotating")
	@. $(VIRTUAL_ENV)/bin/activate && \
	if reuse lint --quiet > /dev/null 2>&1; then \
		echo "All files have proper license headers"; \
	else \
		echo '⚠ REUSE check failed – files are missing proper license headers:'; \
		reuse lint; \
		exit 1; \
	fi
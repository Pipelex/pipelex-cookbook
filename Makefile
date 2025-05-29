ifeq ($(wildcard .env),.env)
include .env
export
endif
VIRTUAL_ENV := $(CURDIR)/.venv
PROJECT_NAME := $(shell grep '^name = ' pyproject.toml | sed -E 's/name = "(.*)"/\1/')

LOCAL_PYTHON := uv run python3.11
LOCAL_PYTEST := uv run pytest

UV_MIN_VERSION = $(shell grep -m1 'required-version' pyproject.toml | sed -E 's/.*= *"([^<>=, ]+).*/\1/')

define PRINT_TITLE
    $(eval PADDED_PROJECT_NAME := $(shell printf '%-15s' "[$(PROJECT_NAME)] " | sed 's/ /=/g'))
    $(eval PADDED_TARGET_NAME := $(shell printf '%-15s' "($@) " | sed 's/ /=/g'))
    $(if $(1),\
		$(eval TITLE := $(shell printf '%s' "=== $(PADDED_PROJECT_NAME) $(PADDED_TARGET_NAME)" | sed 's/[[:space:]]/ /g')$(shell echo " $(1) " | sed 's/[[:space:]]/ /g')),\
		$(eval TITLE := $(shell printf '%s' "=== $(PADDED_PROJECT_NAME) $(PADDED_TARGET_NAME)" | sed 's/[[:space:]]/ /g'))\
	)
	$(eval PADDED_TITLE := $(shell printf '%-126s' "$(TITLE)" | sed 's/ /=/g'))
	@echo ""
	@echo "$(PADDED_TITLE)"
endef

define HELP
Manage $(PROJECT_NAME) located in $(CURDIR).
Usage:

make env                      - Create python virtual env
make lock                     - Refresh uv.lock without updating anything
make install                  - Create local virtualenv & install all dependencies
make update                   - Upgrade dependencies via uv

make format                   - format with ruff format
make lint                     - lint with ruff check
make pyright                  - Check types with pyright
make mypy                     - Check types with mypy

make cleanenv                 - Remove virtual env and lock files
make cleanderived             - Remove extraneous compiled files, caches, logs, etc.
make cleanlibraries           - Remove pipelex_libraries
make cleanall                 - Remove all -> cleanenv + cleanderived + cleanlibraries
make reinitbaselibrary        - Remove pipelex_libraries and init libraries again
make reinstall                - Reinstall dependencies

make merge-check-ruff-lint    - Run ruff merge check without updating files
make merge-check-ruff-format  - Run ruff merge check without updating files
make merge-check-mypy         - Run mypy merge check without updating files
make merge-check-pyright	  - Run pyright merge check without updating files

make rl                       - Shorthand -> reinitlibraries
make ri                       - Shorthand -> reinstall
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

endef
export HELP

.PHONY: all help env lock install update format lint pyright mypy cleanderived cleanenv run-setup s runtests test test-with-prints test-inference t ti test-imgg check cc li merge-check-ruff-lint merge-check-ruff-format merge-check-mypy check-unused-imports fix-unused-imports test-name bump-version check-uv

all help:
	@echo "$$HELP"


##########################################################################################
### SETUP
##########################################################################################

check-uv:
	$(call PRINT_TITLE,"Ensuring uv ≥ $(UV_MIN_VERSION)")
	@command -v uv >/dev/null 2>&1 || { \
		echo "uv not found – installing latest …"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@uv self update >/dev/null 2>&1 || true

env: check-uv
	$(call PRINT_TITLE,"Creating virtual environment")
	@if [ ! -d $(VIRTUAL_ENV) ]; then \
		echo "Creating Python virtual env in \`${VIRTUAL_ENV}\`"; \
		uv venv $(VIRTUAL_ENV) --python 3.11; \
	else \
		echo "Python virtual env already exists in \`${VIRTUAL_ENV}\`"; \
	fi

init: env
	$(call PRINT_TITLE,"Running `pipelex init`")
	pipelex init

install: env
	$(call PRINT_TITLE,"Installing dependencies")
	@. $(VIRTUAL_ENV)/bin/activate && \
	uv pip install -e ".[dev]" && \
	$(VIRTUAL_ENV)/bin/pipelex init && \
	echo "Installed Pipelex cookbook dependencies in ${VIRTUAL_ENV} and initialized Pipelex libraries";

lock: env
	$(call PRINT_TITLE,"Resolving dependencies without update")
	@uv lock && \
	echo "uv lock without update";

update: env
	$(call PRINT_TITLE,"Updating all dependencies")
	@uv pip compile --upgrade pyproject.toml -o requirements.lock && \
	uv pip install -e ".[dev]" && \
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
	find . -name 'requirements.lock' -delete && \
	find . -type d -wholename './.venv' -exec rm -rf {} + && \
	echo "Cleaned up virtual env and dependency lock files";

cleanlock:
	$(call PRINT_TITLE,"Erasing uv lock file")
	@find . -name 'requirements.lock' -delete && \
	echo "Cleaned up uv lock file";

cleanbaselibrary:
	$(call PRINT_TITLE,"Erasing derived files and directories")
	@find . -type d -wholename './pipelex_libraries/pipelines/base_library' -exec rm -rf {} + && \
	echo "Cleaned up pipelex base library";

reinitbaselibrary: cleanbaselibrary init
	@echo "Reinitialized pipelex base library";

reinstall: cleanenv cleanlock install
	@echo "Reinstalled dependencies";

ri: reinstall
	@echo "> done: ri = reinstall"

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
	@uv run ruff format .

lint: env
	$(call PRINT_TITLE,"Linting with ruff")
	@uv run ruff check . --fix

pyright: env
	$(call PRINT_TITLE,"Typechecking with pyright")
	@uv run pyright --pythonpath $(LOCAL_PYTHON)

mypy: env
	$(call PRINT_TITLE,"Typechecking with mypy")
	@uv run mypy


##########################################################################################
### MERGE CHECKS
##########################################################################################

merge-check-ruff-format: env
	$(call PRINT_TITLE,"Formatting with ruff")
	. $(VIRTUAL_ENV)/bin/activate && \
	uv run ruff format --check -v .

merge-check-ruff-lint: env check-unused-imports
	$(call PRINT_TITLE,"Linting with ruff without fixing files")
	. $(VIRTUAL_ENV)/bin/activate && \
	uv run ruff check -v .

merge-check-pyright: env
	$(call PRINT_TITLE,"Typechecking with pyright")
	. $(VIRTUAL_ENV)/bin/activate && \
	uv run pyright -p pyproject.toml

merge-check-mypy: env
	$(call PRINT_TITLE,"Typechecking with mypy")
	. $(VIRTUAL_ENV)/bin/activate && \
	uv run mypy --version && \
	uv run mypy --config-file pyproject.toml

##########################################################################################
### SHORTHANDS
##########################################################################################

check-unused-imports: env
	$(call PRINT_TITLE,"Checking for unused imports without fixing")
	. $(VIRTUAL_ENV)/bin/activate && \
	uv run ruff check --select=F401 --no-fix .

c: init format lint pyright mypy
	@echo "> done: c = check"

cc: init cleanderived c
	@echo "> done: cc = cleanderived check"

check: init cleanderived check-unused-imports c
	@echo "> done: check"

s: init run-setup
	@echo "> done: s = run-setup"

li: lock install
	@echo "> done: lock install"

fix-unused-imports: env
	$(call PRINT_TITLE,"Fixing unused imports")
	. $(VIRTUAL_ENV)/bin/activate && \
	uv run ruff check --select=F401 --fix -v .

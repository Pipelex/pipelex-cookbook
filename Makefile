ifeq ($(wildcard .env),.env)
include .env
export
endif
VIRTUAL_ENV := $(CURDIR)/.venv
PROJECT_NAME := $(shell grep '^name = ' pyproject.toml | sed -E 's/name = "(.*)"/\1/')

# The "?" is used to make the variable optional, so that it can be overridden by the user.
PYTHON_VERSION ?= 3.13
VENV_PYTHON := $(VIRTUAL_ENV)/bin/python
VENV_PYTEST := $(VIRTUAL_ENV)/bin/pytest
VENV_RUFF := $(VIRTUAL_ENV)/bin/ruff
VENV_PYRIGHT := $(VIRTUAL_ENV)/bin/pyright
VENV_MYPY := $(VIRTUAL_ENV)/bin/mypy
VENV_PIPELEX := $(VIRTUAL_ENV)/bin/pipelex
VENV_PLXT := RUST_LOG=warn $(VIRTUAL_ENV)/bin/plxt

UV_MIN_VERSION = $(shell grep -m1 'required-version' pyproject.toml | sed -E 's/.*= *"([^<>=, ]+).*/\1/')

USUAL_PYTEST_MARKERS := "(dry_runnable or not inference) and not (needs_output or pipelex_api)"

define PRINT_TITLE
    $(eval PROJECT_PART := [$(PROJECT_NAME)])
    $(eval TARGET_PART := ($@))
    $(eval MESSAGE_PART := $(1))
    $(if $(MESSAGE_PART),\
        $(eval FULL_TITLE := === $(PROJECT_PART) ===== $(TARGET_PART) ====== $(MESSAGE_PART) ),\
        $(eval FULL_TITLE := === $(PROJECT_PART) ===== $(TARGET_PART) ====== )\
    )
    $(eval TITLE_LENGTH := $(shell echo -n "$(FULL_TITLE)" | wc -c | tr -d ' '))
    $(eval PADDING_LENGTH := $(shell echo $$((126 - $(TITLE_LENGTH)))))
    $(eval PADDING := $(shell printf '%*s' $(PADDING_LENGTH) '' | tr ' ' '='))
    $(eval PADDED_TITLE := $(FULL_TITLE)$(PADDING))
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
make export-requirements      - Export production requirements.txt (no dev dependencies)
make export-requirements-dev  - Export requirements-dev.txt (all dependencies including dev)
make er                       - Shorthand -> export-requirements
make erd                      - Shorthand -> export-requirements-dev
make validate                 - Run the setup sequence to validate the config and libraries

make format                   - Format all (ruff-format + plxt-format)
make lint                     - Lint all (ruff-lint + plxt-lint)
make ruff-format              - Format Python with ruff
make ruff-lint                - Lint Python with ruff
make plxt-format              - Format .mthds/.toml with plxt
make plxt-lint                - Lint .mthds/.toml with plxt
make pyright                  - Check types with pyright
make mypy                     - Check types with mypy

make cleanenv                 - Remove virtual env and lock files
make cleanderived             - Remove extraneous compiled files, caches, logs, etc.
make cleanall                 - Remove all -> cleanenv + cleanderived
make reinstall                - Reinstall dependencies

make merge-check-ruff-lint    - Run ruff merge check without updating files
make merge-check-ruff-format  - Run ruff merge check without updating files
make merge-check-plxt-format  - Check .mthds/.toml formatting with plxt
make merge-check-plxt-lint    - Lint .mthds/.toml with plxt
make merge-check-mypy         - Run mypy merge check without updating files
make merge-check-pyright	  - Run pyright merge check without updating files

make ri                       - Shorthand -> reinstall
make v                        - Shorthand -> validate
make codex-tests              - Run tests for Codex (exit on first failure) (no inference, no codex_disabled)
make gha-tests		          - Run tests for github actions (exit on first failure) (no inference, no gha_disabled)
make test                     - Run unit tests (no inference)
make test-xdist               - Run unit tests with xdist (no inference)
make t                        - Shorthand -> test-xdist
make test-quiet               - Run unit tests without prints (no inference)
make tq                       - Shorthand -> test-quiet
make test-with-prints         - Run tests with prints (no inference)
make tp                       - Shorthand -> test-with-prints
make tb                       - Shorthand -> `make test-with-prints TEST=test_boot`
make test-inference           - Run unit tests only for inference (with prints)
make ti                       - Shorthand -> test-inference

make check                    - Shorthand -> format lint mypy
make c                        - Shorthand -> check
make cc                       - Shorthand -> cleanderived check
make agent-check              - Shorthand -> fix-unused-imports format lint pyright mypy (for AI agents)
make agent-test               - Run unit tests, silent on success, output on failure (for AI agents)
make li                       - Shorthand -> lock install
make check-unused-imports     - Check for unused imports without fixing
make fix-unused-imports       - Fix unused imports with ruff
make fui                      - Shorthand -> fix-unused-imports
make check-TODOs              - Check for TODOs

endef
export HELP

.PHONY: \
	all help env lock install update build \
	export-requirements export-requirements-dev er erd \
	format lint ruff-format ruff-lint plxt-format plxt-lint pyright mypy \
	cleanderived cleanenv cleanall \
	test test-xdist t test-quiet tq test-with-prints tp test-inference ti \
	codex-tests gha-tests \
	run-all-tests run-manual-trigger-gha-tests run-gha_disabled-tests \
	validate v check c cc agent-check agent-test \
	merge-check-ruff-lint merge-check-ruff-format merge-check-plxt-format merge-check-plxt-lint merge-check-mypy merge-check-pyright \
	li check-unused-imports fix-unused-imports check-uv check-TODOs

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
		uv venv $(VIRTUAL_ENV) --python $(PYTHON_VERSION); \
	else \
		echo "Python virtual env already exists in \`${VIRTUAL_ENV}\`"; \
	fi

install: env
	$(call PRINT_TITLE,"Installing dependencies")
	@. $(VIRTUAL_ENV)/bin/activate && \
	uv sync --all-extras && \
	echo "Installed Pipelex cookbook dependencies in ${VIRTUAL_ENV} and initialized Pipelex libraries";

lock: env
	$(call PRINT_TITLE,"Resolving dependencies without update")
	@uv lock && \
	echo "uv lock without update";

update: env
	$(call PRINT_TITLE,"Updating all dependencies")
	@uv lock --upgrade && \
	echo "Updated dependencies in ${VIRTUAL_ENV}";

export-requirements: env
	$(call PRINT_TITLE,"Exporting production requirements")
	@uv export --no-dev --output-file requirements.txt && \
	echo "Exported production requirements to requirements.txt";

export-requirements-dev: env
	$(call PRINT_TITLE,"Exporting development requirements")
	@uv export --all-extras --output-file requirements-dev.txt && \
	echo "Exported all requirements (including dev) to requirements-dev.txt";

er: export-requirements
	@echo "> done: er = export-requirements"

erd: export-requirements-dev
	@echo "> done: erd = export-requirements-dev"

validate: env
	$(call PRINT_TITLE,"Running setup sequence")
	$(VENV_PIPELEX) validate --all

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

reinstall: cleanenv cleanlock install
	@echo "Reinstalled dependencies";

ri: reinstall
	@echo "> done: ri = reinstall"

cleanall: cleanderived cleanenv
	@echo "Cleaned up all derived files and directories";

##########################################################################################
### TESTING
##########################################################################################

codex-tests: env
	$(call PRINT_TITLE,"Unit testing for Codex")
	@echo "• Running unit tests for Codex (excluding inference and codex_disabled)"
	$(VENV_PYTEST) --disable-inference --exitfirst --quiet -m "not inference and not codex_disabled" || [ $$? = 5 ]

gha-tests: env
	$(call PRINT_TITLE,"Unit testing for github actions")
	@echo "• Running unit tests for github actions (excluding inference and gha_disabled)"
	$(VENV_PYTEST) --disable-inference --exitfirst --quiet -m "not inference and not gha_disabled" || [ $$? = 5 ]

run-all-tests: env
	$(call PRINT_TITLE,"Running all unit tests")
	@echo "• Running all unit tests"
	$(VENV_PYTEST) --exitfirst --quiet

run-manual-trigger-gha-tests: env
	$(call PRINT_TITLE,"Running GHA tests")
	@echo "• Running GHA unit tests for inference, llm, and not gha_disabled"
	$(VENV_PYTEST) --exitfirst --quiet -m "not gha_disabled and (inference or llm)" || [ $$? = 5 ]

run-gha_disabled-tests: env
	$(call PRINT_TITLE,"Running GHA disabled tests")
	@echo "• Running GHA disabled unit tests"
	$(VENV_PYTEST) --exitfirst --quiet -m "gha_disabled" || [ $$? = 5 ]

test: env
	$(call PRINT_TITLE,"Unit testing without prints but displaying logs via pytest for WARNING level and above")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(VENV_PYTEST) -s -m $(USUAL_PYTEST_MARKERS) -o log_cli=true -o log_level=WARNING -k "$(TEST)" $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	else \
		$(VENV_PYTEST) -s -m $(USUAL_PYTEST_MARKERS) -o log_cli=true -o log_level=WARNING $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	fi

test-xdist: env
	$(call PRINT_TITLE,"Unit testing without prints but displaying logs via pytest for WARNING level and above")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(VENV_PYTEST) -n auto -m $(USUAL_PYTEST_MARKERS) -o log_level=WARNING -k "$(TEST)" $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	else \
		$(VENV_PYTEST) -n auto -m $(USUAL_PYTEST_MARKERS) -o log_level=WARNING $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	fi

t: test-xdist
	@echo "> done: t = test-xdist"

test-quiet: env
	$(call PRINT_TITLE,"Unit testing without prints but displaying logs via pytest for WARNING level and above")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(VENV_PYTEST) -m $(USUAL_PYTEST_MARKERS) -o log_cli=true -o log_level=WARNING -k "$(TEST)" $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	else \
		$(VENV_PYTEST) -m $(USUAL_PYTEST_MARKERS) -o log_cli=true -o log_level=WARNING $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	fi

tq: test-quiet
	@echo "> done: tq = test-quiet"

test-with-prints: env
	$(call PRINT_TITLE,"Unit testing with prints and our rich logs")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(VENV_PYTEST) -s -m $(USUAL_PYTEST_MARKERS) -k "$(TEST)" $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	else \
		$(VENV_PYTEST) -s -m $(USUAL_PYTEST_MARKERS) $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	fi

tp: test-with-prints
	@echo "> done: tp = test-with-prints"

tb: env
	$(call PRINT_TITLE,"Unit testing a simple boot")
	@echo "• Running unit test test_boot"
	$(VENV_PYTEST) -s -m $(USUAL_PYTEST_MARKERS) -k "test_boot" $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,)));

test-inference: env
	$(call PRINT_TITLE,"Unit testing")
	@if [ -n "$(TEST)" ]; then \
		$(VENV_PYTEST) --pipe-run-mode live --exitfirst -m "inference" -s -k "$(TEST)" $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	else \
		$(VENV_PYTEST) --pipe-run-mode live --exitfirst -m "inference" -s $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	fi

ti: test-inference
	@echo "> done: ti = test-inference"

agent-test: env
	@echo "• Running unit tests..."
	@tmpfile=$$(mktemp); \
	$(VENV_PYTEST) -m $(USUAL_PYTEST_MARKERS) -o log_level=WARNING --tb=short -q > "$$tmpfile" 2>&1; \
	exit_code=$$?; \
	if [ $$exit_code -ne 0 ]; then grep -vE '\[\s*[0-9]+%\]\s*$$' "$$tmpfile"; fi; \
	rm -f "$$tmpfile"; \
	if [ $$exit_code -eq 0 ]; then echo "• All tests passed."; fi; \
	exit $$exit_code

############################################################################################
############################               Linting              ############################
############################################################################################

ruff-format: env
	$(call PRINT_TITLE,"Formatting with ruff")
	@$(VENV_RUFF) format .

ruff-lint: env
	$(call PRINT_TITLE,"Linting with ruff")
	@$(VENV_RUFF) check . --fix

plxt-format: env
	$(call PRINT_TITLE,"Formatting MTHDS/TOML with plxt")
	$(VENV_PLXT) fmt

plxt-lint: env
	$(call PRINT_TITLE,"Linting MTHDS/TOML with plxt")
	$(VENV_PLXT) lint

format: ruff-format plxt-format
	@echo "> done: format = ruff-format plxt-format"

lint: ruff-lint plxt-lint
	@echo "> done: lint = ruff-lint plxt-lint"

pyright: env
	$(call PRINT_TITLE,"Typechecking with pyright")
	$(VENV_PYRIGHT) --pythonpath $(VENV_PYTHON) --project pyproject.toml

mypy: env
	$(call PRINT_TITLE,"Typechecking with mypy")
	@$(VENV_MYPY)


##########################################################################################
### MERGE CHECKS
##########################################################################################

merge-check-ruff-format: env
	$(call PRINT_TITLE,"Formatting with ruff")
	$(VENV_RUFF) format --check -v .

merge-check-ruff-lint: env check-unused-imports
	$(call PRINT_TITLE,"Linting with ruff without fixing files")
	$(VENV_RUFF) check -v .

merge-check-plxt-format: env
	$(call PRINT_TITLE,"Checking MTHDS/TOML formatting with plxt")
	$(VENV_PLXT) fmt --check

merge-check-plxt-lint: env
	$(call PRINT_TITLE,"Linting MTHDS/TOML with plxt")
	$(VENV_PLXT) lint

merge-check-pyright: env
	$(call PRINT_TITLE,"Typechecking with pyright")
	$(VENV_PYRIGHT) --pythonpath $(VENV_PYTHON)

merge-check-mypy: env
	$(call PRINT_TITLE,"Typechecking with mypy")
	$(VENV_MYPY) --version && \
	$(VENV_MYPY) --config-file pyproject.toml

##########################################################################################
### MISCELLANEOUS
##########################################################################################

check-unused-imports: env
	$(call PRINT_TITLE,"Checking for unused imports without fixing")
	$(VENV_RUFF) check --select=F401 --no-fix .

fix-unused-imports: env
	$(call PRINT_TITLE,"Fixing unused imports")
	$(VENV_RUFF) check --select=F401 --fix .

fui: fix-unused-imports
	@echo "> done: fui = fix-unused-imports"

check-TODOs: env
	$(call PRINT_TITLE,"Checking for TODOs")
	@$(VENV_RUFF) check --select=TD -v .

##########################################################################################
### SHORTHANDS
##########################################################################################

c: format lint pyright mypy
	@echo "> done: c = check"

cc: cleanderived c
	@echo "> done: cc = cleanderived check"

check: cleanderived check-unused-imports c
	@echo "> done: check"

agent-check: fix-unused-imports format lint pyright mypy
	@echo "> done: agent-check"

v: validate
	@echo "> done: v = validate"

li: lock install
	@echo "> done: lock install"

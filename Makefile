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
VENV_PLXT := RUST_LOG=warn "$(VIRTUAL_ENV)/bin/plxt"
HEARTBEAT_INTERVAL ?= 20

UV_MIN_VERSION = $(shell grep -m1 'required-version' pyproject.toml | sed -E 's/.*= *"([^<>=, ]+).*/\1/')

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

# Run command $(1) in the background, printing a "$(2) still running (Ns elapsed)" line every
# HEARTBEAT_INTERVAL seconds so long-running targets show progress instead of going silent.
# Leaves the command's exit status in $$exit_code for the caller to act on.
define WAIT_WITH_HEARTBEAT
	start_time=$$(date +%s); \
	$(1) & \
	cmd_pid=$$!; \
	( while kill -0 "$$cmd_pid" 2>/dev/null; do \
		sleep $(HEARTBEAT_INTERVAL); \
		if kill -0 "$$cmd_pid" 2>/dev/null; then \
			elapsed=$$(( $$(date +%s) - $$start_time )); \
			echo "• $(2) still running ($${elapsed}s elapsed)"; \
		fi; \
	done ) & \
	heartbeat_pid=$$!; \
	wait "$$cmd_pid"; \
	exit_code=$$?; \
	kill "$$heartbeat_pid" 2>/dev/null || true; \
	wait "$$heartbeat_pid" 2>/dev/null || true
endef

define HELP
Manage $(PROJECT_NAME) located in $(CURDIR).
Usage:

make env                      - Create python virtual env
make lock                     - Refresh uv.lock without updating anything
make install                  - Create local virtualenv & install all dependencies
make update                   - Upgrade dependencies via uv

make render                   - Write every methods/<name>/README.md from its package and cookbook.toml, and its snippet files under tests/snippets/<name>/
make check-render             - Fail when a committed method page or snippet file differs from a fresh render, or a snippet directory belongs to no method
make check-lockstep           - Fail when a method manifest's version is not the cookbook's
make check-links              - Fetch every sample URL in the packages, and every raw URL on the pages and in the recipes
make check-recipes            - Fail when a recipe's generated types name no pinned address or one its code does not call, when a recipe names an unpinned address, or when its shell script does not parse
make check-codegen            - Check the generated types of every recipe and page snippet against their codegen.lock (offline)
make check-recipe-types       - Type-check every recipe and page snippet: each Python script with pyright in its own environment, each TypeScript package with tsc after its codegen gate, each recipe's shell script with shellcheck
make check-library            - Check that library.json is the snapshot of the library's tarball at the pinned tag (no key)
make check-cookbook           - The checks that need no key: the pages and their snippets, the manifests, the links, the library's snapshot and the recipes (what CI runs)
make refresh-library          - Take the method library's snapshot, library.json, at the tag cookbook.toml pins (no key)
make refresh                  - Take the library's snapshot, write every method's contract.json from production, render, then write every recipe's and page snippet's generated types (needs PIPELEX_API_KEY)
make check-methods            - Validate every method on production from its files (needs PIPELEX_API_KEY)
make check-addresses          - Validate every page's address at its tag, every address a recipe names, and every library method the front page lists, on production (needs PIPELEX_API_KEY)
make check-codegen-live       - Check that every recipe's and page snippet's types come from what its sidecar names as it is today (needs PIPELEX_API_KEY)
make check-hosted             - Every check that calls production, run by hand before each PR and at each release (needs PIPELEX_API_KEY)
make check-smoke              - Run every method once on production on its sample and check its output's shape: SPENDS CREDIT (needs PIPELEX_API_KEY;
                                METHOD=<name> runs one method, ROUTE=address runs each page's address at its tag)
make snapshot METHOD=<name>   - Run one method once on production on its sample and write its output snapshot and its samples' previews:
                                SPENDS CREDIT (needs PIPELEX_API_KEY)

make format                   - format with ruff and plxt
make lint                     - lint with ruff and plxt
make ruff-format              - format with ruff format
make ruff-lint                - lint with ruff check
make plxt-format              - Format MTHDS/TOML files with plxt
make plxt-lint                - Lint MTHDS/TOML files with plxt
make pyright                  - Check types with pyright
make mypy                     - Check types with mypy

make cleanenv                 - Remove virtual env
make cleanderived             - Remove extraneous compiled files, caches, logs, etc.
make cleanall                 - Remove all -> cleanenv + cleanderived
make reinstall                - Reinstall dependencies

make merge-check-ruff-lint    - Run ruff merge check without updating files
make merge-check-ruff-format  - Run ruff merge check without updating files
make merge-check-plxt-format  - Run plxt format check without modifying files
make merge-check-plxt-lint    - Run plxt lint check
make merge-check-mypy         - Run mypy merge check without updating files
make merge-check-pyright	  - Run pyright merge check without updating files

make ri                       - Shorthand -> reinstall
make codex-tests              - Run tests for Codex (exit on first failure) (no codex_disabled)
make gha-tests                - Run tests for github actions (exit on first failure)
make test                     - Run unit tests
make test-xdist               - Run unit tests with xdist
make t                        - Shorthand -> test-xdist
make test-quiet               - Run unit tests without prints
make tq                       - Shorthand -> test-quiet
make test-with-prints         - Run tests with prints
make tp                       - Shorthand -> test-with-prints

make check                    - Shorthand -> format lint mypy
make c                        - Shorthand -> check
make cc                       - Shorthand -> cleanderived check
make agent-check              - Shorthand -> fix-unused-imports format lint pyright mypy check-render check-lockstep check-recipes check-codegen (for AI agents)
make agent-test               - Run unit tests, silent on success, output on failure (for AI agents)
make li                       - Shorthand -> lock install
make check-unused-imports     - Check for unused imports without fixing
make fix-unused-imports       - Fix unused imports with ruff
make fui                      - Shorthand -> fix-unused-imports
make check-TODOs              - Check for TODOs

endef
export HELP

.PHONY: \
	all help env env-verbose check-uv check-uv-verbose lock install update build \
	format lint ruff-format ruff-lint plxt-format plxt-lint pyright mypy \
	cleanderived cleanenv cleanall \
	test test-xdist t test-quiet tq test-with-prints tp \
	codex-tests gha-tests \
	run-all-tests \
	check c cc agent-check agent-test \
	render check-render check-lockstep check-links check-library check-recipes check-codegen check-recipe-types check-cookbook \
	refresh refresh-library check-methods check-addresses check-codegen-live check-hosted check-smoke snapshot \
	merge-check-ruff-lint merge-check-ruff-format merge-check-plxt-format merge-check-plxt-lint merge-check-mypy merge-check-pyright \
	li check-unused-imports fix-unused-imports check-uv check-TODOs

all help:
	@echo "$$HELP"


##########################################################################################
### SETUP
##########################################################################################

# Quiet check-uv: only shows output if uv is missing (needs install)
check-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo ""; \
		echo "=== [$(PROJECT_NAME)] ===== (check-uv) ====== Ensuring uv ≥ $(UV_MIN_VERSION) =========="; \
		echo "uv not found – installing latest …"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@uv self update >/dev/null 2>&1 || true

# Verbose check-uv: always shows output (for setup commands)
check-uv-verbose:
	$(call PRINT_TITLE,"Ensuring uv ≥ $(UV_MIN_VERSION)")
	@command -v uv >/dev/null 2>&1 || { \
		echo "uv not found – installing latest …"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@uv self update >/dev/null 2>&1 || true

# Quiet env: only shows output if venv needs to be created
env: check-uv
	@if [ ! -d $(VIRTUAL_ENV) ]; then \
		echo ""; \
		echo "=== [$(PROJECT_NAME)] ===== (env) ====== Creating virtual environment ================="; \
		echo "Creating Python virtual env in \`${VIRTUAL_ENV}\`"; \
		uv venv $(VIRTUAL_ENV) --python $(PYTHON_VERSION); \
	fi

# Verbose env: always shows output (for setup commands like install, lock, update)
env-verbose: check-uv-verbose
	$(call PRINT_TITLE,"Creating virtual environment")
	@if [ ! -d $(VIRTUAL_ENV) ]; then \
		echo "Creating Python virtual env in \`${VIRTUAL_ENV}\`"; \
		uv venv $(VIRTUAL_ENV) --python $(PYTHON_VERSION); \
	else \
		echo "Python virtual env already exists in \`${VIRTUAL_ENV}\`"; \
	fi

install: env-verbose
	$(call PRINT_TITLE,"Installing dependencies")
	@. $(VIRTUAL_ENV)/bin/activate && \
	uv sync --all-extras && \
	echo "Installed the cookbook's tooling in ${VIRTUAL_ENV}";

lock: env-verbose
	$(call PRINT_TITLE,"Resolving dependencies without update")
	@uv lock && \
	echo "uv lock without update";

update: env-verbose
	$(call PRINT_TITLE,"Updating all dependencies")
	@uv lock --upgrade && \
	echo "Updated dependencies in ${VIRTUAL_ENV}";

##########################################################################################
### METHOD PAGES
##########################################################################################

# The renderer and the checks live in scripts/, and are described in docs/README.md.
# render, check-render and check-lockstep read committed files only. check-links fetches public
# sample URLs and needs no key, and refresh-library and check-library download the method library's public tarball at the pinned tag.
# refresh, check-methods, check-addresses, check-codegen-live and check-hosted call
# production with PIPELEX_API_KEY and spend no inference; CI holds no key, so they are run by hand.
# check-smoke and snapshot are the targets that spend inference credit: check-smoke runs every method once on production, through
# tests/smoke/, whose `smoke` marker pytest's addopts deselect everywhere else, and which skip unless COOKBOOK_SMOKE=1.
# snapshot runs one method once on production and writes what it returned as the method's output snapshot.
#
# A code recipe's generated types come from scripts/sdk/recipe_codegen.py, which runs beside
# pipelex-sdk in an environment of its own (`uv run --script`), so that the trees are written and
# checked with the exact SDK release its inline dependencies pin. It regenerates them (keyed, within refresh), checks them
# against their codegen.lock (offline), and checks that the lock records what the address resolves
# to today (keyed, within check-hosted). Each Python recipe script, and that script itself, is
# type-checked by pyright in the environment its inline dependencies describe, under
# recipes/pyrightconfig.json. Each TypeScript recipe package is installed with npm ci from its own
# lock, then runs its codegen:check script, the pipelex-integrate skill's gate, and tsc --noEmit.
# The page snippets make render writes under tests/snippets/ carry generated types too, whose
# sidecars, which render writes as well, name the package's .mthds files rather than an address,
# so refresh renders before it generates. They are type-checked the same way: each snippet.py by
# pyright in its own environment, under tests/snippets/pyrightconfig.json, which extends the
# recipes' and roots the import of its generated tree beside it, and their one shared TypeScript
# package by tsc, which has no codegen:check script of its own, since check-codegen checks every tree.
# Each recipe's shell script is parsed by `sh -n` within check-recipes and read by shellcheck within
# check-recipe-types. Where shellcheck is not installed, check-recipe-types says so and goes on,
# except in CI, where the runner image carries it and its absence fails the check.
RECIPE_CODEGEN := uv run --quiet --script scripts/sdk/recipe_codegen.py
RECIPE_TREES = $$($(VENV_PYTHON) -m scripts recipe-trees)

render: env
	$(call PRINT_TITLE,"Rendering every method page and its snippet files")
	$(VENV_PYTHON) -m scripts render

check-render: env
	$(call PRINT_TITLE,"Checking that every method page and snippet file matches a fresh render")
	$(VENV_PYTHON) -m scripts check-render

check-lockstep: env
	$(call PRINT_TITLE,"Checking that every method manifest carries the cookbook version")
	$(VENV_PYTHON) -m scripts check-lockstep

check-links: env
	$(call PRINT_TITLE,"Checking every raw sample link")
	$(VENV_PYTHON) -m scripts check-links

check-library: env
	$(call PRINT_TITLE,"Checking the snapshot of the method library against its tarball at the pinned tag")
	$(VENV_PYTHON) -m scripts check-library

check-recipes: env
	$(call PRINT_TITLE,"Checking that every recipe pins the addresses it names and calls and that its shell scripts parse")
	$(VENV_PYTHON) -m scripts check-recipes

check-codegen: env
	$(call PRINT_TITLE,"Checking the generated types of every recipe and page snippet against their codegen.lock")
	@trees="$(RECIPE_TREES)" || exit 1; if [ -n "$$trees" ]; then $(RECIPE_CODEGEN) check $$trees; else echo "no recipe or page snippet carries generated types"; fi

check-recipe-types: env
	$(call PRINT_TITLE,"Type-checking the Python scripts and TypeScript packages of every recipe and page snippet and linting the shell scripts")
	@scripts="$$($(VENV_PYTHON) -m scripts recipe-scripts)" || exit 1; status=0; for script in scripts/sdk/recipe_codegen.py $$scripts; do \
		echo "· $$script"; \
		uv sync --quiet --script "$$script" || { status=1; continue; }; \
		config=recipes/pyrightconfig.json; case "$$script" in tests/snippets/*) config=tests/snippets/pyrightconfig.json;; esac; \
		$(VENV_PYRIGHT) -p "$$config" --pythonpath "$$(uv python find --script "$$script")" "$$script" || status=1; \
	done; \
	packages="$$($(VENV_PYTHON) -m scripts recipe-packages)" || exit 1; for package in $$packages; do \
		echo "· $$package"; \
		(cd "$$package" && npm ci --no-audit --no-fund --loglevel=error && npm run --silent --if-present codegen:check && npx --no-install tsc --noEmit) || status=1; \
	done; \
	shells="$$($(VENV_PYTHON) -m scripts recipe-shell-scripts)" || exit 1; if [ -n "$$shells" ]; then \
		if command -v shellcheck >/dev/null 2>&1; then echo "· shellcheck $$(echo $$shells)"; shellcheck $$shells || status=1; \
		elif [ -n "$${CI:-}" ]; then echo "✗ shellcheck is not installed, and CI runs it over every recipe's shell script"; status=1; \
		else echo "· shellcheck is not installed: the shell scripts were only parsed, by check-recipes"; fi; \
	fi; exit $$status

check-cookbook: check-render check-lockstep check-links check-library check-recipes check-codegen check-recipe-types
	@echo "> done: check-cookbook"

refresh-library: env
	$(call PRINT_TITLE,"Taking the snapshot of the method library at the tag cookbook.toml pins")
	$(VENV_PYTHON) -m scripts refresh-library

refresh: env
	$(call PRINT_TITLE,"Refreshing the library snapshot and the contracts and pages and types")
	$(VENV_PYTHON) -m scripts refresh-library
	$(VENV_PYTHON) -m scripts refresh
	$(VENV_PYTHON) -m scripts render
	@trees="$(RECIPE_TREES)" || exit 1; if [ -n "$$trees" ]; then $(RECIPE_CODEGEN) generate $$trees; fi

check-methods: env
	$(call PRINT_TITLE,"Validating every method on production from its files")
	$(VENV_PYTHON) -m scripts check-methods

check-addresses: env
	$(call PRINT_TITLE,"Validating on production the address of every page at its tag and of every recipe")
	$(VENV_PYTHON) -m scripts check-addresses

check-codegen-live: env
	$(call PRINT_TITLE,"Checking on production that every generated tree comes from what its sidecar names")
	@trees="$(RECIPE_TREES)" || exit 1; if [ -n "$$trees" ]; then $(RECIPE_CODEGEN) verify $$trees; else echo "no recipe or page snippet carries generated types"; fi

check-hosted: check-methods check-addresses check-codegen-live
	@echo "> done: check-hosted"

# METHOD narrows the runs to one method (or several, separated by commas), and ROUTE=address runs each page's address at its tag.
check-smoke: env
	$(call PRINT_TITLE,"Running every method once on production: this spends credit")
	COOKBOOK_SMOKE=1 COOKBOOK_SMOKE_METHOD="$(METHOD)" COOKBOOK_SMOKE_ROUTE="$(ROUTE)" $(VENV_PYTEST) tests/smoke -m smoke -s -p no:sugar -o log_level=WARNING

# Spends inference credit too: one run of METHOD on production, on its sample, whose output becomes its page's "What you get".
snapshot: env
	$(call PRINT_TITLE,"Taking the output snapshot of $(METHOD) from one production run: this spends credit")
	@if [ -z "$(METHOD)" ]; then echo "✗ name the method: make snapshot METHOD=<name>"; exit 1; fi
	$(VENV_PYTHON) -m scripts snapshot "$(METHOD)"

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
	find . -type d -wholename './.venv' -exec rm -rf {} + && \
	echo "Cleaned up virtual env";

reinstall: cleanenv install
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
	@echo "• Running unit tests for Codex (excluding codex_disabled)"
	$(VENV_PYTEST) --exitfirst --quiet -m "not codex_disabled and not smoke" || [ $$? = 5 ]

gha-tests: env
	$(call PRINT_TITLE,"Unit testing for github actions")
	@echo "• Running unit tests for github actions"
	$(VENV_PYTEST) --exitfirst --quiet

run-all-tests: env
	$(call PRINT_TITLE,"Running all unit tests")
	@echo "• Running all unit tests"
	$(VENV_PYTEST) --exitfirst --quiet

test: env
	$(call PRINT_TITLE,"Unit testing without prints but displaying logs via pytest for WARNING level and above")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(VENV_PYTEST) -s -o log_cli=true -o log_level=WARNING -k "$(TEST)" $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	else \
		$(VENV_PYTEST) -s -o log_cli=true -o log_level=WARNING $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	fi

test-xdist: env
	$(call PRINT_TITLE,"Unit testing without prints but displaying logs via pytest for WARNING level and above")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(VENV_PYTEST) -n auto -o log_level=WARNING -k "$(TEST)" $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	else \
		$(VENV_PYTEST) -n auto -o log_level=WARNING $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	fi

t: test-xdist
	@echo "> done: t = test-xdist"

test-quiet: env
	$(call PRINT_TITLE,"Unit testing without prints but displaying logs via pytest for WARNING level and above")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(VENV_PYTEST) -o log_cli=true -o log_level=WARNING -k "$(TEST)" $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	else \
		$(VENV_PYTEST) -o log_cli=true -o log_level=WARNING $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	fi

tq: test-quiet
	@echo "> done: tq = test-quiet"

test-with-prints: env
	$(call PRINT_TITLE,"Unit testing with prints and our rich logs")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(VENV_PYTEST) -s -k "$(TEST)" $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	else \
		$(VENV_PYTEST) -s $(if $(filter 1,$(VERBOSE)),-v,$(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,))); \
	fi

tp: test-with-prints
	@echo "> done: tp = test-with-prints"

agent-test: env
	@echo "• Running unit tests..."
	@tmpfile=$$(mktemp); \
	$(call WAIT_WITH_HEARTBEAT,$(VENV_PYTEST) -o log_level=WARNING --tb=short -q > "$$tmpfile" 2>&1,agent-test); \
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

agent-check: fix-unused-imports format lint pyright mypy check-render check-lockstep check-recipes check-codegen
	@echo "> done: agent-check"

li: lock install
	@echo "> done: lock install"

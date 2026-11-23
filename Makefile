UV ?= uv
CONFIG ?= config.json

.PHONY: install run debug clean lint lint-strict

install:
	$(UV) sync

run:
	$(UV) run python pac-man.py $(CONFIG)

debug:
	$(UV) run python -m pdb pac-man.py $(CONFIG)

clean:
	find . -type d \( -name __pycache__ -o -name .mypy_cache \
		-o -name .pytest_cache \) -prune -exec rm -rf {} +

lint:
	$(UV) run flake8 .
	$(UV) run mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	$(UV) run flake8 .
	$(UV) run mypy . --strict

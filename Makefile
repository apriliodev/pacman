PYTHON ?= python3
CONFIG ?= config.json

.PHONY: install run debug clean lint lint-strict package

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

run:
	$(PYTHON) pac-man.py $(CONFIG)

debug:
	$(PYTHON) -m pdb pac-man.py $(CONFIG)

clean:
	find . -type d \( -name __pycache__ -o -name .mypy_cache \
		-o -name .pytest_cache -o -name build -o -name dist \) \
		-prune -exec rm -rf {} +
	rm -f *.spec.bak

lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict

package:
	$(PYTHON) -m PyInstaller --noconfirm pac-man.spec
	cp config.json PLAYING.txt dist/pac-man/

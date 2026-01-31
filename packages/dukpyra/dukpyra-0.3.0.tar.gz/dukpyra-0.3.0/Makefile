.PHONY: install dev test clean build publish

install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pip install -r requirements-dev.txt

test:
	pytest

clean:
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	python -m build

publish:
	python -m twine upload dist/*

format:
	black dukpyra tests

lint:
	flake8 dukpyra tests
	mypy dukpyra

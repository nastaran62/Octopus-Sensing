SHELL := /bin/bash
.PHONY: help docs mypy test test-coverage publish

help:
	@echo -e "$$(grep -hE '^\S+:.*##' $(MAKEFILE_LIST) | sed -e 's/:.*##\s*/:/' -e 's/^\(.\+\):\(.*\)/\\x1b[36m\1\\x1b[m:\2/' | column -c2 -t -s :)"

docs: ## Generate documents
	cp README.md docs/index.md
	poetry run mkdocs build
	rm docs/index.md

mypy: ## Static type checking
#   Skipping other directories, such as init_script
	poetry run mypy octopus_sensing

test: ## Runs tests
# Integration test mocks lots of modules which intefer with other tests. So, we're running it separately.
	poetry run pytest --full-trace --showlocals octopus_sensing/
	poetry run pytest --full-trace --showlocals octopus_sensing/tests/integration.py

test-coverage: ## Runs tests and reports coverage
# See 'test' comment for why we're running two commands.
	poetry run coverage run -m pytest --full-trace --showlocals octopus_sensing/
	poetry run coverage run --append -m pytest --full-trace --showlocals octopus_sensing/tests/integration.py
	poetry run coverage report

# TODO: PyPi publish
#publish: ## Publishes to PyPi
#publish: mypy test
#	update version
#   commit
#	tag
#	push tag
#	poetry publish

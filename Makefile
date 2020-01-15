.PHONY: test docs package upload

VERSION          ?= $(shell git describe --tags --always --dirty)

default: package

clean:
	rm -fr build dist *egg-info .tox/ .cache/ .pytest_cache/ docs/_build/

.PHONY: install
install:
	poetry install

.PHONY: lint
lint: install
	poetry run pre-commit run --all-files

test: lint install
	poetry run coverage run --source=pykube -m py.test
	poetry run coverage html
	poetry run coverage report

apidocs:
	# update autodoc, only needs to be run when new modules are added
	poetry run sphinx-apidoc pykube -o docs/api/ -T --force

docs:
	poetry run sphinx-build -M html docs docs/_build

package: test
	poetry build

upload: package
	poetry publish

version:
	sed -i 's/__version__ = .*/__version__ = "${VERSION}"/' pykube/__init__.py
	poetry version "${VERSION}"

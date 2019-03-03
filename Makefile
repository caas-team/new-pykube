.PHONY: test package upload

VERSION          ?= $(shell git describe --tags --always --dirty)

default: package

clean:
	rm -fr build dist *egg-info .tox/ .cache/ .pytest_cache/

test:
	pipenv run flake8
	pipenv run coverage run --source=pykube -m py.test
	pipenv run coverage report

package: test
	pipenv run python3 setup.py sdist bdist_wheel
	pipenv run twine check dist/pykube*

upload: package
	pipenv run twine upload dist/pykube*

version:
	sed -i "s/__version__ = .*/__version__ = '${VERSION}'/" pykube/__init__.py

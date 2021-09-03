REQUIREMENTS_TXT ?= requirements.txt requirements-dev.txt
.DEFAULT_GOAL := help

.PHONY: help dev test
include Makefile.venv
Makefile.venv:
	curl \
		-o Makefile.fetched \
		-L "https://github.com/sio/Makefile.venv/raw/v2020.08.14/Makefile.venv"
	echo "5afbcf51a82f629cd65ff23185acde90ebe4dec889ef80bbdc12562fbd0b2611 *Makefile.fetched" \
		| sha256sum --check - \
		&& mv Makefile.fetched Makefile.venv

help:	# Help for the Makefile
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: venv  ## Create the virtualenv with all the requirements installed

docs: build
	cp README.rst docs/readme.rst
	cp Changelog docs/changelog.rst
	tox -edocs

clean: clean-venv  ## Clean out any build artifacts to start over
	rm -rf dist/*

test: dev  ## Run all the tox tests
	tox -p all

build: test  ## Make the build artifact prior to doing an upload
	$(VENV)/python3 setup.py sdist bdist_wheel
	$(VENV)/twine check dist/*

upload: build  ## Upload a new version of the plugin
	$(VENV)/twine upload dist/*

check: dev ## Code format check with tox and pep8
	tox -epep8

fix: dev ## fixes code formatting with gray
	tox -efmt

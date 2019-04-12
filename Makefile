# Run make help to find out what the commands are

.PHONY: deploy_major deploy_minor deploy_patch update_ebnf update_parsers
.PHONY: tests list help clean_pyc clean_build clean_generated dev_install
.PHONY: livedocs

# VDIR = directory of versions
VDIR = bel/lang/versions

YAMLS=$(wildcard $(VDIR)/*.yaml)
EBNFS = $(patsubst $(VDIR)/%.yaml, $(VDIR)/%.ebnf, $(YAMLS))
PARSERS = $(patsubst $(VDIR)/bel%.yaml, $(VDIR)/parser%.py, $(YAMLS))

define deploy_commands
    @echo "Update CHANGELOG"

    git push
	git push --tags
endef


deploy_major:
	@echo Deploying major update
	bumpversion major
	@${deploy_commands}

deploy_minor:
	@echo Deploying minor update
	bumpversion minor
	@${deploy_commands}

deploy_patch:
	@echo Deploying patch update
	bumpversion --allow-dirty patch
	${deploy_commands}

publish:
	setup.py upload

belspec_json:
	belspec_yaml2json

clean_generated:
	rm bel/lang/versions/*.json
	rm bel/lang/versions/parser*
	rm bel/lang/versions/*.ebnf


# Travis CI environment
ci_tests:
	BELTEST='Travis' py.test -rs --cov=./bel -c tests/pytest.ini --color=yes --durations=10 --flakes --pep8 tests


# Local virtualenv test runner with BEL.bio test environment
# add --pdb to get dropped into a debugging env
tests: clean_pyc
	BELTEST='Local' py.test -x -rs --cov=./bel --cov-report html --cov-config .coveragerc -c tests/pytest.ini --color=yes --durations=10 --flakes --pep8 tests


# Run all tests - failing or not
testall: clean_pyc
	BELTEST='Local' py.test -rs --cov=./bel --cov-report html --cov-config .coveragerc -c tests/pytest.ini --color=yes --durations=10 --flakes --pep8 tests


clean_pyc:
	find . -name '*.pyc' -exec rm -r -- {} +
	find . -name '*.pyo' -exec rm -r -- {} +
	find . -name '__pycache__' -exec rm -r -- {} +


clean_build:
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info


dev_install:
	python3.6 -m venv .venv --prompt bel
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install --upgrade setuptools

	.venv/bin/pip install -e .
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -r requirements-docs.txt

livedocs:
	cd docs; sphinx-autobuild -q -p 0 --open-browser --delay 5 source build/html

# TODO
upload: tests
	twine upload

list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'

help:
	@echo "List of commands"
	@echo "   deploy-{major|minor|patch} -- bump version and tag"
	@echo "   help -- This listing "
	@echo "   list -- Automated listing of all targets"
	@echo "   update_ebnf -- Update all EBNF files; requires YAML files inside /versions"
	@echo "   update_parsers -- Update all parser files; requires YAML files inside /versions"

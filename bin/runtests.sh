#!/usr/bin/env bash

# py.test option -rs provides summary of skipped tests
# py.test -rs --exitfirst --cov=./bel --cov-report html --cov-config .coveragerc -c tests/pytest.ini --color=yes --durations=10 --flakes --pep8 tests
py.test -rs --cov=./bel --cov-report html --cov-config .coveragerc -c tests/pytest.ini --color=yes --durations=10 --flakes --pep8 tests

# Added mypy typings checks
# py.test -rs --exitfirst --mypy --cov=./bel --cov-report html --cov-config .coveragerc -c tests/pytest.ini --color=yes --durations=10 --flakes --pep8 tests

# https://www.thapaliya.com/en/writings/well-documented-makefiles/

.DEFAULT_GOAL:=help
SHELL:=/bin/bash

.PHONY: help init


help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

# ##@ Dependencies

# init:  ## Initialize
# 	${INFO} "Creating volumes..."

##@ Testing

# Local virtualenv test runner with BEL.bio test environment
# add --pdb to get dropped into a debugging env
# what is -x used for?


test: clean_pyc  ## Run tests
	BELTEST='Local' py.test -rs --cov=./bel --cov-report html --cov-config .coveragerc --color=yes --durations=10 tests


# Run all tests - failing or not
testall: clean_pyc  ## Run all tests
	BELTEST='Local' cd lib && py.test -rs --cov=./bel --cov-report html --cov-config .coveragerc -c tests/pytest.ini --color=yes --durations=10 tests


##@ Cleaning and Building
clean_pyc:  ## Remove python bytecode
	find . -name '*.pyc' -exec rm -r -- {} +
	find . -name '*.pyo' -exec rm -r -- {} +
	find . -name '__pycache__' -exec rm -r -- {} +


# Push updated bel library to S3 bucket
push_lib:  ## Push bel libraries to S3 bucket
	@poetry build
	aws s3 cp dist/bel-2.0.0.tar.gz s3://resources.bel.bio/packages

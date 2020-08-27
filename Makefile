# https://www.thapaliya.com/en/writings/well-documented-makefiles/

.DEFAULT_GOAL:=help
SHELL:=/bin/bash
CWD := $(abspath $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST))))))

cwd:
	@echo $(CWD)


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


##@ Cleaning and Building
clean_pyc:  ## Remove python bytecode
	find . -name '*.pyc' -exec rm -r -- {} +
	find . -name '*.pyo' -exec rm -r -- {} +
	find . -name '__pycache__' -exec rm -r -- {} +



# Run all tests - failing or not
test_lib: clean_pyc  ## Run BEL library tests
	BELTEST='Local' cd ${CWD}/lib && poetry run py.test -rs --cov=./bel --cov-report html --cov-config .coveragerc --color=yes --durations=10 tests

test_api: clean_pyc  ## Run BEL API tests
	BELTEST='Local' cd ${CWD}/api && poetry run py.test -rs --cov=./app --cov-report html --cov-config .coveragerc --color=yes --durations=10 tests


# Push updated bel library to S3 bucket
push_lib:  ## Push bel libraries to S3 bucket
	@poetry build
	aws s3 cp ${CWD}/dist/bel-2.0.0.tar.gz s3://resources.bel.bio/packages


docker_pushdev:
    @echo Deploying docker DEV image to dockerhub $(VERSION)

    docker build -t belbio/belapi:dev -t belbio/belapi:$(VERSION) -f ./docker/Dockerfile.prod .
    docker push belbio/belapi:dev
    docker push belbio/belapi:$(VERSION)

    ssh thor "cd docker && docker-compose pull belapi"
    ssh thor "cd docker && docker-compose stop belapi"
    ssh thor "cd docker && docker-compose rm -f belapi"
    ssh thor "cd docker && docker-compose up -d belapi"

    @say -v Karen "Finished the BEL A P I docker deployment"


docker_pushprod:
	@echo Deploying docker PROD image to dockerhub $(VERSION)

    docker build -t belbio/belapi:latest -t belbio/belapi:$(VERSION) -f ./docker/Dockerfile.prod .
    docker push belbio/belapi:latest
    docker push belbio/belapi:$(VERSION)

    @say -v Karen "Finished publishing the production BEL A P I docker image"

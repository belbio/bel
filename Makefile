# Run make help to find out what the commands are

.PHONY: deploy-major deploy-minor deploy-patch update_ebnf update_parsers
.PHONY: list help

VERSIONS_DIRECTORY = bel_lang/versions
YAMLS=$(wildcard $(VERSIONS_DIRECTORY)/*.yaml)

define deploy_commands
    @echo "Update CHANGELOG"
    @echo "Create Github release and attach the gem file"

    git push
	git push --tags
endef


deploy-major: update_parsers
	@echo Deploying major update
	bumpversion major
	@${deploy_commands}

deploy-minor: update_parsers
	@echo Deploying minor update
	bumpversion minor
	@${deploy_commands}

deploy-patch: update_parsers
	@echo Deploying patch update
	bumpversion --allow-dirty patch
	${deploy_commands}



update_ebnf: $(YAMLS)

%.yaml: %.ebnf
	python bin/yaml_to_ebnf.py --belspec_fn "$@" --ebnf_fn "$<"

update_parsers: update_ebnf
	./bin/ebnf_to_parsers.py


list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'


help:
	@echo "List of commands"
	@echo "   deploy-{major|minor|patch} -- bump version and tag"
	@echo "   help -- This listing "
	@echo "   list -- Automated listing of all targets"



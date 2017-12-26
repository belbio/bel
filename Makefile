# Run make help to find out what the commands are

.PHONY: deploy-major deploy-minor deploy-patch update_ebnf update_parsers
.PHONY: list help

# VDIR = directory of versions
VDIR = bel_lang/versions

YAMLS=$(wildcard $(VDIR)/*.yaml)
EBNFS = $(patsubst $(VDIR)/%.yaml, $(VDIR)/%.ebnf, $(YAMLS))
PARSERS = $(patsubst $(VDIR)/bel%.yaml, $(VDIR)/parser%.py, $(YAMLS))

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


# set update_ebnf as command dependent on all EBNFs to be made from YAMLs
update_ebnf: $(EBNFS)
	@echo Updating all EBNF files

# each EBNF is dependent upon the corresponding YAML
$(VDIR)/%.ebnf: $(VDIR)/%.yaml
	@echo Turning $< into $@
	python bin/yaml_to_ebnf.py --belspec_fn "$<"

# set update_parsers as command dependent on all PARSER.py files to be made from EBNFs
update_parsers: $(PARSERS)
	@echo Updating all parser files

# each parser file is dependent upon the corresponding EBNF
$(VDIR)/parser%.py: $(VDIR)/bel%.ebnf
	@echo Turning $< into $@
	python bin/ebnf_to_parsers.py --ebnf_fn "$<"

list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'

help:
	@echo "List of commands"
	@echo "   deploy-{major|minor|patch} -- bump version and tag"
	@echo "   help -- This listing "
	@echo "   list -- Automated listing of all targets"
	@echo "   update_ebnf -- Update all EBNF files; requires YAML files inside /versions"
	@echo "   update_parsers -- Update all parser files; requires YAML files inside /versions"

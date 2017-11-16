# Run make help to find out what the commands are

define deploy_commands

    @echo "Update CHANGELOG"
    @echo "Create Github release and attach the gem file"

    git push
	git push --tags
endef

.PHONY: deploy-major
deploy-major:
	@echo Deploying major update
	bumpversion major
	@${deploy_commands}

.PHONY: deploy-minor
deploy-minor:
	@echo Deploying minor update
	bumpversion minor
	@${deploy_commands}

.PHONY: deploy-patch
deploy-patch:
	@echo Deploying patch update
	bumpversion --allow-dirty patch
	${deploy_commands}



.PHONY: list  # ensures list is mis-identified with a file of the same name
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'


.PHONY: help
help:
	@echo "List of commands"
	@echo "   deploy-{major|minor|patch} -- bump version and tag"
	@echo "   help -- This listing "
	@echo "   list -- Automated listing of all targets"

.PHONY: check
check:
	@echo $(HOME)



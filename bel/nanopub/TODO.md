# TODO

1. Test degradation nanopub for for specifying rules
1. Fix up bel_lang scripts to use in bash script for testing
1. [Done]Figure out how to install via pip using github
    1. git+https://github.com/belbio/bel_lang@v0.5.0#egg=bel_lang-0.5.0
    1. git+https://github.com/belbio/bel_nanopub@v0.5.0#egg=bel_nanopub-0.5.0
1. Cut a release of both packages

## Zip up folder of:

    test nanopubs
    belbio_conf.yaml file

## Provide documentation of everything with links to:
    Swagger API - http://apidocs.bel.bio/openapi/index.html
    Kibana Dashboard - https://kibana.bel.bio/app/kibana#/dashboard/AV9JPMFU-sJvDrnqtqsb?_g=()
    How to create and load resources
    How to setup API endpoint

## Test plan:
    Create a bash script to setup virtualenv and install packages

    Create a bash script to test following:

    bel_lang validation
    bel_nanopub validation (last if have time to finish nanopub validation)

    bel_lang orthologization
    bel_lang canonicalization
    bel_lang compute_edges

    bel pipeline
    bel pipeline with rule component_of
    bel pipeline with rule degradation
    bel pipeline with orthologization
    bel pipeline with custom canonicalization

Followup:

1. Figure out what's going on with nested statements in bel pipeline - rework to_string()?
1. Finish nanopub validation

#!/bin/bash


# non-version specific variables ---------------------------------------------------------------------------------------

EBNF_TEMPLATE_FILE="dev/bel.ebnf.j2"
SCRIPT_TO_TEST_PARSER="dev/parser_testing.py"
YAML_TO_EBNF_SCRIPT="dev/yaml_to_ebnf.py"
MULTIPLE_TEST_STATEMENTS="test/bel2_test_statements.txt"
SINGLE_TEST_STATEMENT="test/bel2_test_statement.txt"


# versions -------------------------------------------------------------------------------------------------------------

VERSIONS=(2_0_0 2_0_1)


# build all versions ---------------------------------------------------------------------------------------------------

for v in "${VERSIONS[@]}"
do

    EBNF_SYNTAX_FILE="bel/lang/versions/bel_v$v.ebnf"
    PARSER_PY_FILE="bel/lang/versions/parser_v$v.py"
    YAML_FILE_NAME="bel/lang/versions/bel_v$v.yaml"

    printf "\nBUILDING VERSION %s ********************************************************\n\n" "$v"

    if [[ ! -f ${YAML_FILE_NAME} ]] ; then
        printf "ERROR: %s does not exist! Exiting.\n" "${YAML_FILE_NAME}"
        exit
    fi

    printf "1. Generating syntax EBNF file from YAML...\n"

    python yaml_to_ebnf.py "$YAML_FILE_NAME" "$EBNF_TEMPLATE_FILE" "$EBNF_SYNTAX_FILE"

    printf "2. Generated in %s.\n" "$EBNF_SYNTAX_FILE"
    printf "3. Generating parser file from syntax EBNF file...\n"

    python -m tatsu --generate-parser --outfile "$PARSER_PY_FILE" "$EBNF_SYNTAX_FILE"

    printf "4. Generated in %s.\n" "$PARSER_PY_FILE"
    printf "5. Complete!\n\n\n"

done


# testing --------------------------------------------------------------------------------------------------------------
# python "$SCRIPT_TO_TEST_PARSER" "$SINGLE_TEST_STATEMENT"
# python "$SCRIPT_TO_TEST_PARSER" "$MULTIPLE_TEST_STATEMENTS"

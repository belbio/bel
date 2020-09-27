# Local Imports
# Standard Library
import pprint

# Third Party
import pytest

# Local
import bel.lang.ast
from bel.schemas.bel import AssertionStr, ValidationError

# cSpell:disable

# TODO test reading in a string from a file doesn't remove the escape backslash


@pytest.mark.skip(msg="Cannot handle escaped quote")
def test_ast_parse():

    # Bad quote
    # assertion = AssertionStr(entire='complex(SCOMP:"Test named\" complex", p(HGNC:"207"!"AKT1 Test), p(HGNC:207!"Test"), loc(nucleus)) increases p(HGNC:EGF) increases p(hgnc : "here I am" ! X)')

    assertion = AssertionStr(
        entire='complex(SCOMP:"Test named" complex", p(HGNC:"207"!"AKT1 Test"), p(HGNC:207!"Test"), loc(nucleus)) increases p(HGNC:EGF) increases p(hgnc : "here I am" ! X)'
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.print_tree()

    print("\n")

    for arg in ast.args:
        print("AST arg: ", arg)

    assert "complexAbundance" == ast.args[0].name

    assert "increases" == ast.args[1].name

    assert "proteinAbundance(HGNC:EGF)" == str(ast.args[2])


def test_ast_orthologization():
    """Test AST orthologization"""

    assertion = AssertionStr(entire="p(HGNC:AKT1)")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    if ast.orthologizable("TAX:10090"):
        ast.orthologize("TAX:10090")

        print("Orthologized to mouse", ast.to_string())
        assert ast.to_string() == "p(EG:11651!Akt1)"

        ast.decanonicalize()

        print("Orthologized and decanonicalized to mouse", ast.to_string())

        assert ast.to_string() == "p(SP:P31750!Akt1)"

    else:
        assert False, "Not orthologizable"


def test_ast_orthologizable():
    """Test AST orthologization"""

    # No rat ortholog for human EG:9
    assertion = AssertionStr(entire="p(HGNC:AKT1) increases p(EG:9)")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    result = ast.orthologizable("TAX:10116")  # orthologizable to Rat

    assert result == False

    result = ast.orthologizable("TAX:10090")  # orthologizable to mouse

    assert result == True


#####################################################################################
# Validation tests                                                              #####
#####################################################################################


def test_validate_simple_function():
    """Validate simple function"""

    assertion = AssertionStr(entire="p(HGNC:AKT1)")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_missing_namespace():
    """Validate simple function"""

    assertion = AssertionStr(entire="p(missing:AKT1)")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert (
        ast.errors[0].msg
        == "Unknown namespace value 'missing:AKT1' for the proteinAbundance function at position 2"
    )
    assert ast.errors[0].severity == "Warning"


def test_validate_empty_function():
    """Validate empty function"""

    assertion = AssertionStr(entire="p()")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == "No arguments in function: proteinAbundance"
    assert ast.errors[0].severity == "Error"


def test_validate_empty_modifier():
    """Validate empty modifier"""

    assertion = AssertionStr(entire="p(HGNC:AKT1, frag())")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == "No arguments in function: fragment"
    assert ast.errors[0].severity == "Error"


def test_validate_frag_function():
    """Validate functions"""

    assertion = AssertionStr(entire='p(HGNC:AKT1, frag("26_141"))')

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_deg_function():
    """Validate functions"""

    assertion = AssertionStr(entire='deg(a(CHEBI:"intermediate-density lipoprotein"))')

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("p(HGNC:HRAS, pmod(Ac))", []),
        ("p(HGNC:HRAS, pmod(Ac, S, 473))", []),
        ("p(HGNC:HRAS, pmod(Ac, Ser, 473))", []),
    ],
)
def test_validate_pmod_function(test_input, expected):
    """Accept Single or three letter Amino Acid code"""

    assertion = AssertionStr(entire=test_input)

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            "p(HGNC:HRAS, pmod(Ac, , 473))",
            "String Argument 473 not found in ['AminoAcid'] default BEL namespaces",
        ),
        (
            "p(HGNC:HRAS, pmod(,,473))",
            "String Argument 473 not found in ['ProteinModification'] default BEL namespaces",
        ),
    ],
)
def test_validate_pmod_function_errors(test_input, expected):
    """Accept Single or three letter Amino Acid code"""

    assertion = AssertionStr(entire=test_input)

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == expected


def test_validate_complex_missing_namespace():
    """Validate path()"""

    assertion = AssertionStr(subject="complex(UNKNOWN:test)")
    expected = (
        "Unknown namespace value UNKNOWN:test - cannot determine if this matches function signature"
    )
    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == expected


def test_abundance_namespace():
    """Validate path()"""

    assertion = AssertionStr(
        subject="a(CHEBI:15377!water)",
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_reaction():
    """Validate reaction"""

    assertion = AssertionStr(
        subject='rxn(reactants(a(CHEBI:"vitamin A"), a(CHEBI:NAD)), products(a(SCHEM:Retinaldehyde)))'
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors")
    for error in ast.errors:
        print("    ", error.json(), "\n")

    assert ast.errors == []


def test_validation_tloc():
    """Validate reaction"""

    assertion = AssertionStr(subject="tloc(p(MGI:Lipe), fromLoc(GO:0005737), toLoc(GO:0005811))")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_fus():
    """Validate path()"""

    assertion = AssertionStr(subject='p(fus(HGNC:NPM, "1_117", HGNC:ALK, end))')
    expected = "Wrong entity type for namespace argument at position 0 for function fusion - expected ['Gene', 'RNA', 'Micro_RNA', 'Protein'], actual: entity_types: []"

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == expected


def test_validate_nsarg():
    """Validate path()"""

    assertion = AssertionStr(subject="path(DO:COVID-19)")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_obsolete_nsarg():

    assertion = AssertionStr(subject="r(HGNC:A2MP)")
    expected = "BEL Entity name is obsolete - please update to HGNC:8!A2MP1"

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == expected


def test_validate_nested():

    assertion = AssertionStr(
        subject="p(HGNC:CCL5)",
        relation="decreases",
        object='(p(HGNC:CXCL12) increases bp(GO:"platelet aggregation"))',
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_rxn1():
    """Validate path()"""

    assertion = AssertionStr(
        subject="rxn(reactants(complex(reactome:R-HSA-1112584.1, p(SP:O14543, loc(GO:0005829)))), products(complex(reactome:R-HSA-1112584.1, p(SP:O14543), loc(GO:0005829))))"
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Parse Info", ast.parse_info)

    print("Errors")
    for error in ast.errors:
        print("Error", error.json())

    assert ast.errors == []


def test_validate_complex_nsarg():

    assertion = AssertionStr(
        subject='p(HGNC:PTHLH) increases act(complex(SCOMP:"Nfkb Complex"), ma(tscript))'
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_bad_relation():

    assertion = AssertionStr(subject="p(HGNC:PTHLH) XXXincreases p(HGNC:PTHLH)")
    expected = "Could not parse Assertion - bad relation: XXXincreases"
    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == expected


def test_validate_missing_parts():
    """Test object only or missing object or relation bel assertion"""

    assertion = AssertionStr(object="p(HGNC:AKT1)")
    ast = bel.lang.ast.BELAst(assertion=assertion)

    print("Validation messages - object only")
    for error in ast.errors:
        print("    ", error.json(), "\n")

    assert ast.errors[0].msg == "Missing Assertion Subject or Relation"

    assertion = AssertionStr(relation="increases")
    ast = bel.lang.ast.BELAst(assertion=assertion)

    print("Validation messages - relation only")
    for error in ast.errors:
        print("    ", error.json(), "\n")

    assert ast.errors[0].msg == "Missing Assertion Object"

    assertion = AssertionStr(relation="increases", object="p(HGNC:AKT1)")
    ast = bel.lang.ast.BELAst(assertion=assertion)

    print("Validation messages - relation and object")
    for error in ast.errors:
        print("    ", error.json(), "\n")

    assert ast.errors[0].msg == "Missing Assertion Subject or Relation"

    assertion = AssertionStr(subject="p(HGNC:AKT1)", object="p(HGNC:AKT1)")
    ast = bel.lang.ast.BELAst(assertion=assertion)

    print("Validation messages - subject and object")
    for error in ast.errors:
        print("    ", error.json(), "\n")

    assert ast.errors[0].msg == "Missing Assertion Subject or Relation"


#####################################################################################
# Canonicalization tests                                                        #####
#####################################################################################


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("p(HGNC:AKT1)", "p(EG:207!AKT1)"),
        ("complex(p(HGNC:IL12B), p(HGNC:IL12A))", "complex(p(EG:3592!IL12A), p(EG:3593!IL12B))"),
        (
            'complex(loc(GO:"extracellular space"), p(HGNC:IL12A), p(EG:207), p(HGNC:IL12B))',
            'complex(p(EG:207!AKT1), p(EG:3592!IL12A), p(EG:3593!IL12B), loc(GO:0005615!"extracellular space"))',
        ),
        (
            'complex(p(HGNC:MTOR), a(CHEBI:"phosphatidic acid"), a(CHEBI:sirolimus))',
            'complex(a(CHEBI:16337!"phosphatidic acid"), a(CHEBI:9168!sirolimus), p(EG:2475!MTOR))',
        ),
        (
            'rxn(reactants(a(CHEBI:hypoxanthine), a(CHEBI:water), a(CHEBI:dioxygen)), products(a(CHEBI:xanthine), a(CHEBI:"hydrogen peroxide"))',
            'rxn(reactants(a(CHEBI:15377!water), a(CHEBI:15379!dioxygen), a(CHEBI:17368!hypoxanthine)), products(a(CHEBI:15318!xanthine), a(CHEBI:16240!"hydrogen peroxide")))',
        ),
        (
            "p(HGNC:MAPK1, pmod(Ph, Thr, 185), pmod(Ph, Tyr, 187), pmod(Ph))",
            "p(EG:5594!MAPK1, pmod(Ph), pmod(Ph, Thr, 185), pmod(Ph, Tyr, 187))",
        ),
        (
            "p(HGNC:KRAS, pmod(Palm, Cys), pmod(Ph, Tyr, 32))",
            "p(EG:3845!KRAS, pmod(Palm, Cys), pmod(Ph, Tyr, 32))",
        ),
        (
            "p(HGNC:TP53, var(p.His168Arg), var(p.Arg249Ser))",
            "p(EG:7157!TP53, var(p.Arg249Ser), var(p.His168Arg))",
        ),
        (
            "p(HGNC:NFE2L2, pmod(Ac, Lys, 596), pmod(Ac, Lys, 599), loc(GO:nucleus))",
            "p(EG:4780!NFE2L2, loc(GO:0005634!nucleus), pmod(Ac, Lys, 596), pmod(Ac, Lys, 599))",
        ),
    ],
)
def test_ast_canonicalization(test_input, expected):
    """Test AST canonicalization and sorting function arguments

    See issue: https://github.com/belbio/bel/issues/13
    """

    assertion = AssertionStr(entire=test_input)

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.canonicalize()

    print("Canonicalized", ast.to_string())

    assert ast.to_string() == expected

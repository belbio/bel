# Standard Library
import json
import pprint

# Third Party
import pytest

# Local
import bel.lang.ast
from bel.schemas.bel import AssertionStr, ValidationError

# cSpell:disable

# TODO path(DO:COVID-19) decreases a("glycyl-L-leucine)  - causes exception


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
        == "Unknown BEL Entity 'missing:AKT1' for the proteinAbundance function at position 2"
    )
    assert ast.errors[0].severity == "Warning"


def test_validate_strarg():

    assertion = AssertionStr(subject='complex("missing")')
    expected = "String argument not allowed as an optional or multiple argument. Probably missing a namespace."

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == expected


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
        "Unknown BEL Entity UNKNOWN:test - cannot determine if this matches function signature"
    )
    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == expected


def test_validate_abundance_namespace():
    """Validate abundance namespace"""

    assertion = AssertionStr(
        subject="a(CHEBI:15377!water)",
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_namespace_using_synonyms():
    """Validate nsarg that doesn't match alt_keys but does match synonyms"""

    assertion = AssertionStr(
        subject="p(MGI:Emr4)",
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

    assertion = AssertionStr(
        subject='tloc(p(HGNC:NFE2L2), fromLoc(MESH:Cytoplasm), toLoc(MESH:"Cell Nucleus"))'
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []

    assertion = AssertionStr(
        subject='tloc(complex(p(HGNC:NFE2L2), p(HGNC:PLK1)), fromLoc(MESH:Cytoplasm), toLoc(MESH:"Cell Nucleus"))'
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_fus1():
    """Validate fus()"""

    # HGNC:NPM isn't valid - but it gets converted to updated entity
    assertion = AssertionStr(subject='p(fus(HGNC:NPM, "1_117", HGNC:ALK, end))')

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_fus2():
    """Validate fus()"""

    assertion = AssertionStr(subject="p(fus(HGNC:EWSR1, start, HGNC:FLI1, end))")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_fus3():
    """Validate fus()"""

    assertion = AssertionStr(subject='r(fus(HGNC:TMPRSS2, "?", HGNC:ERG, "?"))')

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_fus4():
    """Validate fus()"""

    assertion = AssertionStr(
        subject='r(fus(HGNC:11876!TMPRSS2, "r.1_79", HGNC:3446!ERG, "r.312_5034"))'
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_fus5():
    """Validate fus()"""

    assertion = AssertionStr(subject='r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034"))')

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_fus6():
    """Validate fus()"""

    assertion = AssertionStr(
        subject="""p(fus(SP:P11274!BCR, “1-585”, SP:P11362!FGFR1, “429-585”), pmod(PSIMOD:00048!O4'-phospho-L-tyrosine))"""
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_sec():
    """Validate fus()"""

    assertion = AssertionStr(
        subject='bp(GO:0030168!"platelet activation")',
        relation="increases",
        object='sec(a(SCHEM:"Thymosin beta(4)"))',
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


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

    assert ast.errors[0].msg == "Reaction should not have equivalent reactants and products"


def test_validate_rxn2():
    """Validate path()"""

    assertion = AssertionStr(
        subject='rxn(reactants(a(CHEBI:"guanidinoacetic acid"), a(CHEBI:"(S)-S-adenosyl-L-methionine")), products(a(CHEMBL:s-adenosylhomocysteine), a(CHEBI:creatine)))'
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors")
    for error in ast.errors:
        print("Error", error.json())

    assert ast.errors == []


def test_validate_rxn3():
    """Validate path()"""

    assertion = AssertionStr(
        entire='act(p(HGNC:GPT2), ma(cat)) directlyIncreases rxn(reactants(a(CHEBI:alanine), a(SCHEM:"alpha-Ketoglutaric acid")), products(a(SCHEM:"Propanoic acid, 2-oxo-, ion(1-)"), a(CHEBI:"L-glutamic acid")))'
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors")
    for error in ast.errors:
        print("Error", error.json())

    assert ast.errors == []


def test_validate_rxn4():
    """Validate path()"""

    assertion = AssertionStr(subject="rxn(reactants(g(HGNC:AKT1)), products(g(HGNC:AKT2)))")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

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

    assertion = AssertionStr(subject='complex(GO:"transcription factor AP-1 complex")')

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


def test_validate_complex_nsarg_quoted_colon():

    assertion = AssertionStr(subject='complex(SCOMP:"KLF1:SWI/SNF complex")')

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert (
        ast.errors[0].msg
        == 'Unknown BEL Entity SCOMP:"KLF1:SWI/SNF complex" - cannot determine if this matches function signature'
    )


def test_validate_bad_relation():

    assertion = AssertionStr(subject="p(HGNC:PTHLH) XXXincreases p(HGNC:PTHLH)")
    expected = "Could not parse Assertion - bad relation? XXXincreases"
    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == expected


def test_validate_bad_function():

    assertion = AssertionStr(subject="ppp(HGNC:PTHLH)")
    expected = "Could not parse Assertion - bad relation? HGNC:9607!PTHLH"
    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == expected


def test_validate_bad_nsarg():

    assertion = AssertionStr(subject="p(HGNC:)")
    expected = "Could not match function: proteinAbundance arguments to BEL Specification"
    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == expected


def test_validate_missing_right_quote():

    assertion = AssertionStr(subject='p(HGNC:"AKT1)')
    expected = "Missing right quote after left quote at position 7 and before position 13"
    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors[0].msg == expected


def test_validate_missing_left_quote():

    assertion = AssertionStr(subject='p(HGNC:AKT1")')
    expected = "Missing left quote before right quote at position 11"
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


def test_validate_extra_parts():

    assertion = AssertionStr(
        subject="""tloc(complex(a(CHEBI:29101!"sodium(1+)"), a(CHEBI:57427!"L-leucine zwitterion")), fromLoc(GO:0005576!"extracellular region"), toLoc(GO:0005829!cytosol))  tloc(a(CHEBI:32682!"L-argininium(1+)"), fromLoc(GO:0005829!cytosol), toLoc(GO:0005576!"extracellular region"))""",
        relation="directlyIncreases",
        object="""tloc(complex(a(CHEBI:29101!"sodium(1+)"), a(CHEBI:57427!"L-leucine zwitterion")), fromLoc(GO:0005576!"extracellular region"), toLoc(GO:0005829!cytosol))""",
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    if ast.errors:
        print("Validation messages - subject and object")
        for error in ast.errors:
            print("    ", error.json(), "\n")

    assert ast.errors[0].msg.startswith("Could not parse Assertion - bad relation")


def test_validate_rxn_semantics():

    # ERROR reactants(A, B) -> products(complex(A, B))  SHOULD BE complex(A, B)
    assertion = AssertionStr(
        subject="rxn(reactants(p(HGNC:AKT1), p(HGNC:AKT2)), products(complex(p(HGNC:AKT1), p(HGNC:AKT2))))"
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Validation Errors", ast.errors)

    assert (
        ast.errors[0].msg
        == "Reaction should be replaced with just the product complex: complex(p(HGNC:391!AKT1), p(HGNC:392!AKT2))"
    )

    # ERROR reactants(A, B) SHOULD NOT EQUAL products(A, B)
    assertion = AssertionStr(
        subject="rxn(reactants(p(HGNC:AKT1), p(HGNC:AKT2)), products(p(HGNC:AKT1), p(HGNC:AKT2)))"
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Validation Errors", ast.errors)

    assert ast.errors[0].msg == "Reaction should not have equivalent reactants and products"

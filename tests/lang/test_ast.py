# Local Imports
import bel.lang.ast
import pytest
from bel.schemas.bel import AssertionStr

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
        assert ast.to_string() == "p(EG:11651)"

        ast.decanonicalize()

        print("Orthologized and decanonicalized to mouse", ast.to_string())

        assert ast.to_string() == "p(SP:P31750)"

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

    assert ast.errors == [('WARNING', "Unknown namespace 'missing' at position 0 for function proteinAbundance")]


def test_validate_empty_function():
    """Validate empty function"""

    assertion = AssertionStr(entire="p()")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == [("ERROR", "No arguments in function: proteinAbundance")]


def test_validate_empty_modifier():
    """Validate empty modifier"""

    assertion = AssertionStr(entire="p(HGNC:AKT1, frag())")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == [("ERROR", "No arguments in function: fragment")]


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
        ("p(HGNC:HRAS, pmod(Ac, , 473))", [('ERROR', "String Argument 473 not found in ['AminoAcid'] default BEL namespaces")]),
        ("p(HGNC:HRAS, pmod(,,473))", [('ERROR', "String Argument 473 not found in ['ProteinModification'] default BEL namespaces")]),
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


def test_validate_path_and_namespace():
    """Validate path()"""

    assertion = AssertionStr(entire='path(DO:COVID-19)')

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.validate()

    print("Errors", ast.errors)

    assert ast.errors == []


#####################################################################################
# Canonicalization tests                                                        #####
#####################################################################################


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("p(HGNC:AKT1)", "p(EG:207)"),
        ("complex(p(HGNC:IL12B), p(HGNC:IL12A))", "complex(p(EG:3592), p(EG:3593))"),
        (
            'complex(loc(GO:"extracellular space"), p(HGNC:IL12A), p(EG:207), p(HGNC:IL12B))',
            'complex(p(EG:207), p(EG:3592), p(EG:3593), loc(GO:0005615))',
        ),
        (
            'complex(p(HGNC:MTOR), a(CHEBI:"phosphatidic acid"), a(CHEBI:sirolimus))',
            'complex(a(CHEBI:16337), a(CHEBI:9168), p(EG:2475))',
        ),
        (
            'rxn(reactants(a(CHEBI:hypoxanthine), a(CHEBI:water), a(CHEBI:dioxygen)), products(a(CHEBI:xanthine), a(CHEBI:"hydrogen peroxide"))',
            'rxn(reactants(a(CHEBI:15377), a(CHEBI:15379), a(CHEBI:17368)), products(a(CHEBI:15318), a(CHEBI:16240)))',
        ),
        (
            "p(HGNC:MAPK1, pmod(Ph, Thr, 185), pmod(Ph, Tyr, 187), pmod(Ph))",
            "p(EG:5594, pmod(Ph), pmod(Ph, Thr, 185), pmod(Ph, Tyr, 187))",
        ),
        (
            "p(HGNC:KRAS, pmod(Palm, Cys), pmod(Ph, Tyr, 32))",
            "p(EG:3845, pmod(Palm, Cys), pmod(Ph, Tyr, 32))",
        ),
        (
            "p(HGNC:TP53, var(p.His168Arg), var(p.Arg249Ser))",
            "p(EG:7157, var(p.Arg249Ser), var(p.His168Arg))",
        ),
        (
            "p(HGNC:NFE2L2, pmod(Ac, Lys, 596), pmod(Ac, Lys, 599), loc(GO:nucleus))",
            "p(EG:4780, loc(GO:0005634), pmod(Ac, Lys, 596), pmod(Ac, Lys, 599))",
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

    assert ast.to_string() == expected

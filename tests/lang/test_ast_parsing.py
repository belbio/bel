# Standard Library
import json
import pprint

# Third Party
import pytest

# Local
import bel.lang.ast
from bel.schemas.bel import AssertionStr, ValidationError

# cSpell:disable

# TODO test reading in a string from a file doesn't remove the escape backslash


@pytest.mark.skip(msg="Cannot handle escaped quote")
def test_ast_parse_escaped_quote():

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

        assert ast.to_string() == "p(MGI:87986!Akt1)"

    else:
        assert False, "Not orthologizable"


def test_ast_nested_orthologization():

    assertion = AssertionStr(entire="p(HGNC:AKT1) increases (p(HGNC:AKT1) increases p(HGNC:EGF))")
    ast = bel.lang.ast.BELAst(assertion=assertion)

    orthologizable = ast.orthologizable("TAX:10090")
    print("Orthologizable", orthologizable)

    ast.orthologize("TAX:10090").decanonicalize()

    expected = "p(MGI:87986!Akt1) increases (p(MGI:87986!Akt1) increases p(MGI:95290!Egf))"

    result = ast.to_string()
    print("Result", result)

    assert result == expected


def test_ast_orthologizable():
    """Test AST orthologization"""

    # No rat ortholog for human EG:9
    assertion = AssertionStr(entire="p(HGNC:AKT1) increases p(EG:9)")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    result = ast.orthologizable("TAX:10116")  # orthologizable to Rat

    assert result == False

    result = ast.orthologizable("TAX:10090")  # orthologizable to mouse

    assert result == True


def test_ast_parse_fus():

    assertion = AssertionStr(entire="act(p(fus(HGNC:EWSR1, start, HGNC:FLI1, end)), ma(tscript))")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    print("To String", ast.to_string())

    assert (
        ast.to_string() == "act(p(fus(HGNC:3508!EWSR1, start, HGNC:3749!FLI1, end)), ma(tscript))"
    )


def test_get_species():
    """Collect all NSArg species for Assertion"""

    assertion = AssertionStr(entire="p(HGNC:391!AKT1) increases p(MGI:87986!Akt1)")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    species = ast.get_species_keys()

    print("Species", species)

    assert species == ["TAX:9606", "TAX:10090"]


@pytest.mark.skip("Figure out a better way to handle checks")
def test_get_orthologs():
    """Get all orthologs for any NSArgs in Assertion"""

    assertion = AssertionStr(entire="p(MGI:Akt2) increases p(HGNC:391!AKT1)")

    ast = bel.lang.ast.BELAst(assertion=assertion)

    orthologs = ast.get_orthologs()

    print("Orthologs")
    for ortholog in orthologs:
        print(ortholog)

    expected = [
        {
            "TAX:10090": {"canonical": "EG:11652", "decanonical": "MGI:104874"},
            "TAX:9606": {"canonical": "EG:208", "decanonical": "HGNC:392"},
            "TAX:10116": {"canonical": "EG:25233", "decanonical": "RGD:2082"},
        },
        {
            "TAX:9606": {"canonical": "EG:207", "decanonical": "HGNC:391"},
            "TAX:10116": {"canonical": "EG:24185", "decanonical": "RGD:2081"},
            "TAX:10090": {"canonical": "EG:11651", "decanonical": "MGI:87986"},
        },
    ]

    # orthologs - compares the string result of the NSVal object for the orthologs

    assert orthologs == expected

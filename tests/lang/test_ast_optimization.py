# Standard Library
import json
import pprint

# Third Party
import pytest

# Local
import bel.lang.ast
from bel.lang.ast import Function
from bel.schemas.bel import AssertionStr, ValidationError

# cSpell:disable


def test_rxn_complex_1():
    """Simple rxn -> complex

    rxn(A, B) -> rxn(complex(A, B))  ==> complex(A, B)
    """

    assertion = AssertionStr(
        subject="rxn(reactants(p(HGNC:AKT1), p(HGNC:AKT2)), products(complex(p(HGNC:AKT1), p(HGNC:AKT2)))"
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.optimize()

    print("complex(): ", ast.to_string())

    assert ast.to_string() == "complex(p(HGNC:391!AKT1), p(HGNC:392!AKT2))"


def test_rxn_complex_2():
    """More complex rxn -> complex"""
    assertion = AssertionStr(
        subject="rxn(reactants(g(ensembl:ENSG00000157557!ETS2), p(SP:P50548!ERF, loc(GO:0005654!nucleoplasm))), products(complex(g(ensembl:ENSG00000157557!ETS2), p(SP:P50548!ERF), loc(GO:0005654!nucleoplasm))))"
    )
    expected = (
        "complex(g(ensembl:ENSG00000157557!ETS2), p(SP:P50548!ERF), loc(GO:0005654!nucleoplasm))"
    )
    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.optimize()

    print("complex(): ", ast.to_string())

    assert ast.to_string() == expected


def test_rxn_tloc():
    """rxn to tloc"""
    assertion = AssertionStr(
        subject="""rxn(reactants(p(HGNC:391!AKT1, loc(GO:nucleus))), products(p(HGNC:391!AKT1, loc(GO:cytosol))))"""
    )
    expected = "tloc(p(HGNC:391!AKT1), fromLoc(GO:0005634!nucleus), toLoc(GO:0005829!cytosol))"

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.optimize()

    print("tloc(): ", ast.to_string())

    assert ast.to_string() == expected


def test_rxn_surf():

    assertion = AssertionStr(
        subject="""rxn(reactants(p(HGNC:391!AKT1, loc(GO:nucleus))), products(p(HGNC:391!AKT1, loc(GO:"plasma membrane"))))"""
    )
    expected = "surf(p(HGNC:391!AKT1))"

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.optimize()

    print("surf(): ", ast.to_string())

    assert ast.to_string() == expected


def test_rxn_sec():

    assertion = AssertionStr(
        subject="""rxn(reactants(p(HGNC:391!AKT1, loc(GO:nucleus))), products(p(HGNC:391!AKT1, loc(GO:"extracellular region"))))"""
    )
    expected = "sec(p(HGNC:391!AKT1))"

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.optimize()

    print("sec(): ", ast.to_string())

    assert ast.to_string() == expected


def test_tloc_sec():

    assertion = AssertionStr(
        subject="""tloc(p(HGNC:391!AKT1), fromLoc(GO:nucleus), toLoc(GO:"extracellular region"))"""
    )
    expected = "sec(p(HGNC:391!AKT1))"

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.optimize()

    print("sec(): ", ast.to_string())

    assert ast.to_string() == expected


def test_tloc_surf():

    assertion = AssertionStr(
        subject="""tloc(p(HGNC:391!AKT1), fromLoc(GO:nucleus), toLoc(GO:"plasma membrane"))"""
    )
    expected = "surf(p(HGNC:391!AKT1))"

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.optimize()

    print("Surf(): ", ast.to_string())

    assert ast.to_string() == expected


def test_optimization_subject_only():
    """Relation and Object are None values"""

    assertion = AssertionStr(subject="p(HGNC:AKT1)", relation=None, object=None)

    expected = "p(HGNC:391!AKT1)"

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.optimize()

    print("Optimized(): ", ast.to_string())

    assert ast.to_string() == expected


def test_optimization_misc_1():
    """Misc"""

    assertion = AssertionStr(
        subject='rxn(reactants(a(CHEBI:30616!"ATP(4-)", loc(GO:0005829!cytosol)), complex(p(SP:O14641!DVL2, pmod(PSIMOD:00696!"phosphorylated residue")), p(SP:Q9NPB6!PARD6A), loc(GO:0005829!cytosol))), products(a(CHEBI:456216!"ADP(3-)", loc(GO:0005654!nucleoplasm)), complex(p(SP:O14641!DVL2, pmod(PSIMOD:00696!"phosphorylated residue")), p(SP:Q9NPB6!PARD6A), loc(GO:0005829!cytosol))))',
        relation=None,
        object=None,
    )

    expected = """ """

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.optimize()

    print("Misc optimized(): ", ast.to_string())

    assert ast.to_string() == expected


# def test_optimization_misc_3():
#     """Misc"""

#     assertion = AssertionStr(
#         subject="""act(complex(p(SP:Q13535!ATR), p(SP:Q8WXE1!ATRIP), loc(GO:0005654!nucleoplasm)))""",
#         relation="directlyIncreases",
#         object="""rxn(reactants(a(CHEBI:30616!"ATP(4-)", loc(GO:0005654!nucleoplasm)), complex(p(CHEBI:36080!protein), p(SP:O00311!CDC7), p(SP:O43913!ORC5), p(SP:O43929!ORC4), p(SP:O75419!CDC45), p(SP:P24941!CDK2), p(SP:P25205!MCM3), p(SP:P33991!MCM4), p(SP:P33992!MCM5), p(SP:P33993!MCM7), p(SP:P49736!MCM2), p(SP:Q13415!ORC1), p(SP:Q13416!ORC2), p(SP:Q14566!MCM6), p(SP:Q7L590!MCM10), p(SP:Q99741!CDC6), p(SP:Q9HAW4!CLSPN), p(SP:Q9UBD5!ORC3), p(SP:Q9UBU7!DBF4), p(SP:Q9UJA3!MCM8), p(SP:Q9Y5N6!ORC6), p(reactome:R-ALL-68419.2!"origin of replication"), loc(GO:0005654!nucleoplasm))), products(a(CHEBI:456216!"ADP(3-)", loc(GO:0005654!nucleoplasm)), complex(p(CHEBI:36080!protein), p(SP:O00311!CDC7), p(SP:O43913!ORC5), p(SP:O43929!ORC4), p(SP:O75419!CDC45), p(SP:P24941!CDK2), p(SP:P25205!MCM3), p(SP:P33991!MCM4), p(SP:P33992!MCM5), p(SP:P33993!MCM7), p(SP:P49736!MCM2), p(SP:Q13415!ORC1), p(SP:Q13416!ORC2), p(SP:Q14566!MCM6), p(SP:Q7L590!MCM10), p(SP:Q99741!CDC6), p(SP:Q9HAW4!CLSPN, pmod(Ph, Ser, 945), pmod(Ph, Thr, 916)), p(SP:Q9UBD5!ORC3), p(SP:Q9UBU7!DBF4), p(SP:Q9UJA3!MCM8), p(SP:Q9Y5N6!ORC6), p(reactome:R-ALL-68419.2!"origin of replication"), loc(GO:0005654!nucleoplasm))))""",
#     )

#     expected = """ """

#     ast = bel.lang.ast.BELAst(assertion=assertion)

#     ast.optimize()

#     print("Misc optimized(): ", ast.to_string())

#     assert ast.to_string() == expected

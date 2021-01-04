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


def test_optimize_rxn_1():
    """Optimize rxn 1

    rxn(A, B) -> rxn(complex(A, B))  ==> complex(A, B)
    """

    assertion = AssertionStr(
        subject="rxn(reactants(p(HGNC:AKT1), p(HGNC:AKT2)), products(complex(p(HGNC:AKT1), p(HGNC:AKT2)))"
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.optimize()

    print("RXN", ast.to_string())

    assert ast.to_string() == "complex(p(HGNC:391!AKT1), p(HGNC:392!AKT2))"


def test_optimize_rxn_2():
    assertion = AssertionStr(
        subject="rxn(reactants(g(ensembl:ENSG00000157557!ETS2), p(SP:P50548!ERF, loc(GO:0005654!nucleoplasm))), products(complex(g(ensembl:ENSG00000157557!ETS2), p(SP:P50548!ERF), loc(GO:0005654!nucleoplasm))))"
    )

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.optimize()

    print("RXN", ast.to_string())

    assert (
        ast.to_string()
        == "complex(g(ensembl:ENSG00000157557!ETS2), p(SP:P50548!ERF), loc(GO:0005654!nucleoplasm))"
    )

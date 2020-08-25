# Local Imports
import bel.core.settings as settings
import bel.edge.computed
import bel.lang.belobj
from bel.schemas.bel import AssertionStr

bo = bel.lang.belobj.BEL()


def test_simple_complex():

    assertion = AssertionStr(entire="complex(p(HGNC:AKT1))")

    check_edges = [
        "complex(p(HGNC:AKT1)) hasComponent p(HGNC:AKT1)",
    ]

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = [str(edge) for edge in edges]

    print("Edges", edges)

    assert check_edges == edges


def test_named_complex():

    assertion = AssertionStr(entire="complex(SCOMP:AKT)")

    check_edges = []

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = [str(edge) for edge in edges]

    assert check_edges == edges


def test_complex():

    assertion = AssertionStr(
        entire="complex(p(HGNC:AKT1), p(HGNC:EGF)) increases act(p(HGNC:AKT2), ma(kin))"
    )

    check_edges = sorted(
        [
            "complex(p(HGNC:AKT1), p(HGNC:EGF)) hasComponent p(HGNC:AKT1)",
            "complex(p(HGNC:AKT1), p(HGNC:EGF)) hasComponent p(HGNC:EGF)",
            "p(HGNC:AKT2) hasActivity act(p(HGNC:AKT2), ma(kin))",
        ]
    )

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = sorted([str(edge) for edge in edges])

    assert check_edges == edges


def test_act():

    assertion = AssertionStr(entire="act(p(HGNC:AKT2), ma(kin))")

    check_edges = ["p(HGNC:AKT2) hasActivity act(p(HGNC:AKT2), ma(kin))"]

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = [str(edge) for edge in edges]

    assert check_edges == edges


def test_pmod():

    assertion = AssertionStr(entire="p(HGNC:AKT1, pmod(Ph, S, 473))")

    check_edges = ["p(HGNC:AKT1) hasModification p(HGNC:AKT1, pmod(Ph, S, 473))"]

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = [str(edge) for edge in edges]

    assert check_edges == edges


def test_var():

    assertion = AssertionStr(entire='p(HGNC:CFTR, var("p.Gly576Ala"))')

    check_edges = ['p(HGNC:CFTR) hasVariant p(HGNC:CFTR, var("p.Gly576Ala"))']

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = [str(edge) for edge in edges]

    assert check_edges == edges


def test_frag():

    assertion = AssertionStr(entire='p(HGNC:YFG, frag("5_20"))')

    check_edges = ['p(HGNC:YFG) hasFragment p(HGNC:YFG, frag("5_20"))']

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = [str(edge) for edge in edges]

    assert check_edges == edges


def test_loc():

    assertion = AssertionStr(entire='a(CHEBI:"calcium(2+)", loc(GO:"endoplasmic reticulum"))')

    check_edges = [
        'a(CHEBI:"calcium(2+)") hasLocation a(CHEBI:"calcium(2+)", loc(GO:"endoplasmic reticulum"))'
    ]

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = [str(edge) for edge in edges]

    assert check_edges == edges


def test_tloc():

    assertion = AssertionStr(
        entire='tloc(p(HGNC:EGFR), fromLoc(GO:"cell surface"), toLoc(GO:endosome))'
    )

    check_edges = sorted(
        [
            'tloc(p(HGNC:EGFR), fromLoc(GO:"cell surface"), toLoc(GO:endosome)) decreases p(HGNC:EGFR, loc(GO:"cell surface"))',
            'tloc(p(HGNC:EGFR), fromLoc(GO:"cell surface"), toLoc(GO:endosome)) increases p(HGNC:EGFR, loc(GO:endosome))',
            'p(HGNC:EGFR) hasLocation p(HGNC:EGFR, loc(GO:"cell surface"))',
            "p(HGNC:EGFR) hasLocation p(HGNC:EGFR, loc(GO:endosome))",
        ]
    )

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = sorted([str(edge) for edge in edges])

    assert check_edges == edges


def test_surf_and_sec():

    assertion = AssertionStr(entire="surf(p(HGNC:EGFR))")

    check_edges = sorted(
        [
            'surf(p(HGNC:EGFR)) increases p(HGNC:EGFR, loc(GO:0009986!"cell surface"))',
            'p(HGNC:EGFR) hasLocation p(HGNC:EGFR, loc(GO:0009986!"cell surface"))',
        ]
    )

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = sorted([str(edge) for edge in edges])

    assert check_edges == edges

    assertion = AssertionStr(entire="sec(p(MGI:Il6))")

    check_edges = sorted(
        [
            'sec(p(MGI:Il6)) increases p(MGI:Il6, loc(GO:0005615!"extracellular space"))',
            'p(MGI:Il6) hasLocation p(MGI:Il6, loc(GO:0005615!"extracellular space"))',
        ]
    )

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = sorted([str(edge) for edge in edges])

    assert check_edges == edges


def test_fus():

    assertion = AssertionStr(entire='r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034"))')

    check_edges = sorted(
        [
            'r(HGNC:TMPRSS2) hasFusion r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034"))',
            'r(HGNC:ERG) hasFusion r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034"))',
        ]
    )

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = sorted([str(edge) for edge in edges])

    assert check_edges == edges


def test_deg():

    assertion = AssertionStr(
        entire="act(p(HGNC:HSD11B1), ma(cat)) increases deg(a(SCHEM:Hydrocortisone))"
    )

    check_edges = sorted(
        [
            "deg(a(SCHEM:Hydrocortisone)) directlyDecreases a(SCHEM:Hydrocortisone)",
            "p(HGNC:HSD11B1) hasActivity act(p(HGNC:HSD11B1), ma(cat))",
        ]
    )

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = sorted([str(edge) for edge in edges])

    assert check_edges == edges


def test_rxn():

    assertion = AssertionStr(
        entire='rxn(reactants(a(CHEBI:superoxide)),products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen)))'
    )

    check_edges = sorted(
        [
            'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen))) hasReactant a(CHEBI:superoxide)',
            'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen))) hasProduct a(CHEBI:"hydrogen peroxide")',
            'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen))) hasProduct a(CHEBI:oxygen)',
        ]
    )

    parsed = bo.parse(assertion)

    edges = bel.edge.computed.computed_edges(parsed.ast)
    edges = sorted([str(edge) for edge in edges])

    assert check_edges == edges

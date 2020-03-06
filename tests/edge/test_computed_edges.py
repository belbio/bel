# Local Imports
import bel.edge.computed
import bel.lang.belobj
from bel.Config import config

bo = bel.lang.belobj.BEL(
    config["bel"]["lang"]["default_bel_version"], config["bel_api"]["servers"]["api_url"]
)


def test_complex():

    belstr = "complex(p(HGNC:AKT1), p(HGNC:EGF)) increases act(p(HGNC:AKT2), ma(kin))"
    check_edges = [
        "complex(p(HGNC:AKT1), p(HGNC:EGF)) hasComponent p(HGNC:AKT1)",
        "complex(p(HGNC:AKT1), p(HGNC:EGF)) hasComponent p(HGNC:EGF)",
        "p(HGNC:AKT2) hasActivity act(p(HGNC:AKT2), ma(kin))",
    ]

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)

    for edge in edges:
        print(str(edge))
        assert str(edge) in check_edges


def test_act():

    belstr = "act(p(HGNC:AKT2), ma(kin))"
    check_edges = ["p(HGNC:AKT2) hasActivity act(p(HGNC:AKT2), ma(kin))"]

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)

    for edge in edges:
        assert str(edge) in check_edges


def test_pmod():

    belstr = "p(HGNC:AKT1, pmod(Ph, S, 473))"
    check_edges = ["p(HGNC:AKT1) hasModification p(HGNC:AKT1, pmod(Ph, S, 473))"]

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)
    for edge in edges:
        assert str(edge) in check_edges


def test_var():

    belstr = 'p(HGNC:CFTR, var("p.Gly576Ala"))'
    check_edges = ['p(HGNC:CFTR) hasVariant p(HGNC:CFTR, var("p.Gly576Ala"))']

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)
    for edge in edges:
        assert str(edge) in check_edges


def test_frag():

    belstr = 'p(HGNC:YFG, frag("5_20"))'
    check_edges = ['p(HGNC:YFG) hasFragment p(HGNC:YFG, frag("5_20"))']

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)
    for edge in edges:
        assert str(edge) in check_edges


def test_loc():

    belstr = 'a(CHEBI:"calcium(2+)", loc(GO:"endoplasmic reticulum"))'
    check_edges = [
        'a(CHEBI:"calcium(2+)") hasLocation a(CHEBI:"calcium(2+)", loc(GO:"endoplasmic reticulum"))'
    ]

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)
    for edge in edges:
        assert str(edge) in check_edges


def test_tloc():

    belstr = 'tloc(p(HGNC:EGFR), fromLoc(GO:"cell surface"), toLoc(GO:endosome))'
    check_edges = [
        'tloc(p(HGNC:EGFR), fromLoc(GO:"cell surface"), toLoc(GO:endosome)) decreases p(HGNC:EGFR, loc(GO:"cell surface"))',
        'tloc(p(HGNC:EGFR), fromLoc(GO:"cell surface"), toLoc(GO:endosome)) increases p(HGNC:EGFR, loc(GO:endosome))',
        'p(HGNC:EGFR) hasLocation p(HGNC:EGFR, loc(GO:"cell surface"))',
        "p(HGNC:EGFR) hasLocation p(HGNC:EGFR, loc(GO:endosome))",
    ]

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)

    assert str(edges[0]) == check_edges[0]

    for edge in edges:
        assert str(edge) in check_edges


def test_surf_and_sec():

    belstr = "surf(p(HGNC:EGFR))"
    check_edges = [
        'surf(p(HGNC:EGFR)) increases p(HGNC:EGFR, loc(GO:"cell surface"))',
        'p(HGNC:EGFR) hasLocation p(HGNC:EGFR, loc(GO:"cell surface"))',
    ]

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)

    for edge in edges:
        assert str(edge) in check_edges

    belstr = "sec(p(MGI:Il6))"
    check_edges = [
        'sec(p(MGI:Il6)) increases p(MGI:Il6, loc(GO:"extracellular space"))',
        'p(MGI:Il6) hasLocation p(MGI:Il6, loc(GO:"extracellular space"))',
    ]

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)
    for edge in edges:
        assert str(edge) in check_edges


def test_fus():

    belstr = 'r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034"))'
    check_edges = [
        'r(HGNC:TMPRSS2) hasFusion r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034"))',
        'r(HGNC:ERG) hasFusion r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034"))',
    ]

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)
    for edge in edges:
        assert str(edge) in check_edges


def test_deg():
    belstr = "act(p(HGNC:HSD11B1), ma(cat)) increases deg(a(SCHEM:Hydrocortisone))"
    check_edges = [
        "deg(a(SCHEM:Hydrocortisone)) directlyDecreases a(SCHEM:Hydrocortisone)",
        "p(HGNC:HSD11B1) hasActivity act(p(HGNC:HSD11B1), ma(cat))",
    ]

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)
    for edge in edges:
        assert str(edge) in check_edges


def test_rxn():

    belstr = 'rxn(reactants(a(CHEBI:superoxide)),products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen)))'
    check_edges = [
        'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen))) hasReactant a(CHEBI:superoxide)',
        'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen))) hasProduct a(CHEBI:"hydrogen peroxide")',
        'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:oxygen))) hasProduct a(CHEBI:oxygen)',
    ]

    parsed = bo.parse(belstr)

    edges = bel.edge.computed.compute_edges(parsed.ast, bo.spec)
    for edge in edges:
        assert str(edge) in check_edges

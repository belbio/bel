import bel_lang
from bel_lang.defaults import defaults

bel_obj = bel_lang.BEL(defaults['bel_version'], defaults['belapi_endpoint'])


def test_abundance():

    statement = 'abundance(CHEBI:corticosteroid) decreases biologicalProcess(MESHD:Inflammation)'
    expected_edges = ['CHEBI:corticosteroid componentOf abundance(CHEBI:corticosteroid)',
                      'MESHD:Inflammation componentOf biologicalProcess(MESHD:Inflammation)'
                      ]

    actual_edges = bel_obj.parse(statement).computed()

    assert set(expected_edges) == set(actual_edges)


def test_complex():

    statement = 'p(HGNC:TNF) increases act(complex(SCOMP:"Nfkb Complex"), ma(tscript))'
    expected_edges = ['HGNC:TNF componentOf p(HGNC:TNF)',
                      'SCOMP:"Nfkb Complex" componentOf complex(SCOMP:"Nfkb Complex")',
                      'complex(SCOMP:"Nfkb Complex") componentOf act(complex(SCOMP:"Nfkb Complex"), ma(tscript))',
                      'ma(tscript) componentOf act(complex(SCOMP:"Nfkb Complex"), ma(tscript))'
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_composite():

    statement = 'composite(p(HGNC:VEGFA), p(HGNC:FN1)) increases act(p(HGNC:PRKCA), ma(kin))'
    expected_edges = ['HGNC:VEGFA componentOf p(HGNC:VEGFA)',
                      'HGNC:FN1 componentOf p(HGNC:FN1)',
                      'p(HGNC:VEGFA) componentOf composite(p(HGNC:VEGFA), p(HGNC:FN1))',
                      'p(HGNC:FN1) componentOf composite(p(HGNC:VEGFA), p(HGNC:FN1))',
                      'HGNC:PRKCA componentOf p(HGNC:PRKCA)',
                      'p(HGNC:PRKCA) componentOf act(p(HGNC:PRKCA), ma(kin))',
                      'ma(kin) componentOf act(p(HGNC:PRKCA), ma(kin))'
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_g():

    statement = 'g(REF:"NM_000492.3", var("c.1521_1523delCTT")) association bp(GOBP:"wound healing")'
    expected_edges = ['REF:"NM_000492.3" componentOf g(REF:"NM_000492.3", var("c.1521_1523delCTT"))',
                      'GOBP:"wound healing" componentOf bp(GOBP:"wound healing")',
                      'var("c.1521_1523delCTT") componentOf g(REF:"NM_000492.3", var("c.1521_1523delCTT"))'
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_m():

    statement = 'microRNAAbundance(MGI:Mir21)'
    expected_edges = ['MGI:Mir21 componentOf {}'.format(statement)
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_p():

    statement = 'p(HGNC:AKT1, loc(MESHCS:Cytoplasm)) increases p(HGNC:EGFR, loc(MESHCS:Cytoplasm))'
    expected_edges = ['HGNC:AKT1 componentOf p(HGNC:AKT1, loc(MESHCS:Cytoplasm))',
                      'loc(MESHCS:Cytoplasm) componentOf p(HGNC:AKT1, loc(MESHCS:Cytoplasm))',
                      'MESHCS:Cytoplasm componentOf loc(MESHCS:Cytoplasm)',
                      'HGNC:EGFR componentOf p(HGNC:EGFR, loc(MESHCS:Cytoplasm))',
                      'loc(MESHCS:Cytoplasm) componentOf p(HGNC:EGFR, loc(MESHCS:Cytoplasm))',
                      'MESHCS:Cytoplasm componentOf loc(MESHCS:Cytoplasm)',
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_r():

    statement = 'proteinAbundance(HGNC:IL6) increases rnaAbundance(HGNC:ENO1)'
    expected_edges = ['HGNC:IL6 componentOf proteinAbundance(HGNC:IL6)',
                      'HGNC:ENO1 componentOf rnaAbundance(HGNC:ENO1)'
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_bp():

    statement = 'act(p(HGNC:KDR), ma(kin)) association bp(GOBP:"cell death")'
    expected_edges = ['HGNC:KDR componentOf p(HGNC:KDR)',
                      'p(HGNC:KDR) componentOf act(p(HGNC:KDR), ma(kin))',
                      'GOBP:"cell death" componentOf bp(GOBP:"cell death")',
                      'ma(kin) componentOf act(p(HGNC:KDR), ma(kin))'
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_path():

    statement = 'pathology(MESH:Psoriasis) isA pathology(MESH:"Skin Diseases")'
    expected_edges = ['MESH:Psoriasis componentOf pathology(MESH:Psoriasis)',
                      'MESH:"Skin Diseases" componentOf pathology(MESH:"Skin Diseases")'
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_act():

    statement = 'act(complex(NCH:"ENaC Complex"), ma(GOMF:"transporter activity"))'
    expected_edges = ['NCH:"ENaC Complex" componentOf complex(NCH:"ENaC Complex")',
                      'GOMF:"transporter activity" componentOf ma(GOMF:"transporter activity")',
                      'complex(NCH:"ENaC Complex") componentOf {}'.format(statement),
                      'ma(GOMF:"transporter activity") componentOf {}'.format(statement)
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_tloc():

    statement = 'tloc(p(HGNC:NFE2L2), fromLoc(MESHCL:Cytoplasm), toLoc(MESHCL:"Cell Nucleus"))'
    expected_edges = ['HGNC:NFE2L2 componentOf p(HGNC:NFE2L2)',
                      'MESHCL:Cytoplasm componentOf fromLoc(MESHCL:Cytoplasm)',
                      'MESHCL:"Cell Nucleus" componentOf toLoc(MESHCL:"Cell Nucleus")',
                      'p(HGNC:NFE2L2) componentOf {}'.format(statement),
                      'fromLoc(MESHCL:Cytoplasm) componentOf {}'.format(statement),
                      'toLoc(MESHCL:"Cell Nucleus") componentOf {}'.format(statement)
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_sec():

    statement = 'p(HGNC:F2) increases sec(a(CHEBI:"nitric oxide"))'
    expected_edges = ['HGNC:F2 componentOf p(HGNC:F2)',
                      'CHEBI:"nitric oxide" componentOf a(CHEBI:"nitric oxide")',
                      'a(CHEBI:"nitric oxide") componentOf sec(a(CHEBI:"nitric oxide"))'
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_surf():

    statement = 'a(CHEBI:"nitric oxide") increases surf(complex(p(HGNC:ITGA2), p(HGNC:ITGB1)))'
    expected_edges = ['CHEBI:"nitric oxide" componentOf a(CHEBI:"nitric oxide")',
                      'HGNC:ITGA2 componentOf p(HGNC:ITGA2)',
                      'HGNC:ITGB1 componentOf p(HGNC:ITGB1)',
                      'p(HGNC:ITGA2) componentOf complex(p(HGNC:ITGA2), p(HGNC:ITGB1))',
                      'p(HGNC:ITGB1) componentOf complex(p(HGNC:ITGA2), p(HGNC:ITGB1))',
                      'complex(p(HGNC:ITGA2), p(HGNC:ITGB1)) componentOf surf(complex(p(HGNC:ITGA2), p(HGNC:ITGB1)))'
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_deg():

    statement = 'act(p(SFAM:"MAPK p38 Family"), ma(GO:"kinase activity")) decreases deg(p(HGNC:HBP1))'
    expected_edges = ['SFAM:"MAPK p38 Family" componentOf p(SFAM:"MAPK p38 Family")',
                      'GO:"kinase activity" componentOf ma(GO:"kinase activity")',
                      'p(SFAM:"MAPK p38 Family") componentOf act(p(SFAM:"MAPK p38 Family"), ma(GO:"kinase activity"))',
                      'ma(GO:"kinase activity") componentOf act(p(SFAM:"MAPK p38 Family"), ma(GO:"kinase activity"))',
                      'HGNC:HBP1 componentOf p(HGNC:HBP1)',
                      'p(HGNC:HBP1) componentOf deg(p(HGNC:HBP1))',
                      'deg(p(HGNC:HBP1)) directlyDecreases p(HGNC:HBP1)'
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_rxn():

    statement = 'rxn(reactants(a(CHEBI:superoxide)), products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:"oxygen")))'
    expected_edges = ['CHEBI:superoxide componentOf a(CHEBI:superoxide)',
                      'CHEBI:"hydrogen peroxide" componentOf a(CHEBI:"hydrogen peroxide")',
                      'CHEBI:"oxygen" componentOf a(CHEBI:"oxygen")',
                      'a(CHEBI:superoxide) componentOf reactants(a(CHEBI:superoxide))',
                      'a(CHEBI:"hydrogen peroxide") componentOf products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:"oxygen"))',
                      'a(CHEBI:"oxygen") componentOf products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:"oxygen"))',
                      'reactants(a(CHEBI:superoxide)) componentOf {}'.format(statement),
                      'products(a(CHEBI:"hydrogen peroxide"), a(CHEBI:"oxygen")) componentOf {}'.format(statement)
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


def test_list():

    statement = 'p(SFAM:"MAPK JNK Family") hasMembers list(p(HGNC:MAPK8), p(HGNC:MAPK9))'
    expected_edges = ['SFAM:"MAPK JNK Family" componentOf p(SFAM:"MAPK JNK Family")',
                      'HGNC:MAPK8 componentOf p(HGNC:MAPK8)',
                      'HGNC:MAPK9 componentOf p(HGNC:MAPK9)',
                      'p(HGNC:MAPK8) componentOf list(p(HGNC:MAPK8), p(HGNC:MAPK9))',
                      'p(HGNC:MAPK9) componentOf list(p(HGNC:MAPK8), p(HGNC:MAPK9))'
                      ]

    actual_edges = bel_obj.parse(statement).computed()
    assert set(expected_edges) == set(actual_edges)


# def test_computed_list_function():
#
#     s = 'list(p(HGNC:MAPK8), p(HGNC:MAPK9))'
#     expected = ['{} hasMember p(HGNC:MAPK8)'.format(s),
#                 '{} hasMember p(HGNC:MAPK9)'.format(s)]
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result
#
#     s = 'list(p(HGNC:CAV1, pmod(Ph, Y, 14)), p(HGNC:SLC2A4))'
#     expected = ['{} hasMember p(HGNC:CAV1, pmod(Ph, Y, 14))'.format(s),
#                 '{} hasMember p(HGNC:SLC2A4)'.format(s),
#                 'p(HGNC:CAV1) hasModification p(HGNC:CAV1, pmod(Ph, Y, 14))']
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result
#
#     s = 'list(p(MGI:Il6), bp(MESHPP:Apoptosis), path(MESHD:Inflammation))'
#     expected = ['{} hasMember p(MGI:Il6)'.format(s),
#                 '{} hasMember bp(MESHPP:Apoptosis)'.format(s),
#                 '{} hasMember path(MESHD:Inflammation)'.format(s)]
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result
#
#
# def test_computed_composite_function():
#
#     s = 'composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng))'
#     expected = ['{} hasMember a(SCHEM:Lipopolysaccharide)'.format(s),
#                 '{} hasMember p(MGI:Ifng)'.format(s)]
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result
#
#     s = 'composite(p(HGNC:IL6), complex(GOCC:"interleukin-23 complex"))'
#     expected = ['{} hasMember p(HGNC:IL6)'.format(s),
#                 '{} hasMember complex(GOCC:"interleukin-23 complex")'.format(s),
#                 'complex(GOCC:"interleukin-23 complex") hasComponent GOCC:"interleukin-23 complex"']
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result
#
#     s = 'compositeAbundance(proteinAbundance(HGNC:TGFB1), proteinAbundance(HGNC:IL6))'
#     expected = ['{} hasMember proteinAbundance(HGNC:TGFB1)'.format(s),
#                 '{} hasMember proteinAbundance(HGNC:IL6)'.format(s)]
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result
#
#     s = 'composite(p(SFAM:"Histone H3 Family", pmod(Ac)), p(SFAM:"Histone H4 Family", pmod(Ac)))'
#     expected = ['{} hasMember p(SFAM:"Histone H3 Family", pmod(Ac))'.format(s),
#                 '{} hasMember p(SFAM:"Histone H4 Family", pmod(Ac))'.format(s),
#                 'p(SFAM:"Histone H3 Family") hasModification p(SFAM:"Histone H3 Family", pmod(Ac))',
#                 'p(SFAM:"Histone H4 Family") hasModification p(SFAM:"Histone H4 Family", pmod(Ac))']
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result
#
#
# def test_computed_deg_function():
#     s = 'deg(r(HGNC:MYC))'
#     expected = ['{} directlyDecreases r(HGNC:MYC)'.format(s)]
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result
#
#
# def test_computed_act_function():
#     s = 'act(p(MGI:Met), ma(kin))'
#     expected = ['p(MGI:Met) hasActivity {}'.format(s)]
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result
#
#
# def test_computed_var_function():
#     s = 'r(HGNC:CFTR, var("c.1521_1523delCTT"))'
#     expected = ['r(HGNC:CFTR) hasVariant {}'.format(s)]
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result
#
#
# def test_computed_fus_function():
#     s = 'p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))'
#     expected = ['p(HGNC:BCR) hasFusion {}'.format(s),
#                 'p(HGNC:JAK2) hasFusion {}'.format(s)]
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result
#
#
# def test_computed_pmod_function():
#     s = 'p(HGNC:AKT1, pmod(P, S, 473))'
#     expected = ['p(HGNC:AKT1) hasModification {}'.format(s)]
#     result = bel_obj.computed(bel_obj.parse(s).ast)
#     assert sorted(expected) == result

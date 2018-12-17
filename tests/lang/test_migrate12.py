import bel.lang.migrate_1_2
import pytest


@pytest.mark.skip(reason="Skip for now - need to implement this functionality - maybe")
def test_migrate_naked_entities():

    bel1 = "kin(MGI:Lck)"
    bel2 = "act(p(MGI:Lck), ma(DEFAULT:kin))"

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2

    bel1 = 'tloc(HGNC:CTNNB1)'
    bel2 = 'tloc(p(HGNC:CTNNB1))'
    assert bel.lang.migrate_1_2.migrate(bel1) == bel2


def test_migrate():

    # No migration examples
    bel1 = 'sec(a(CHEBI:"3-hydroxybutyrate"))'
    bel2 = 'sec(a(CHEBI:3-hydroxybutyrate))'

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2

    # kin() -> activity()
    # bel1 = 'p(HGNC:BRAF,sub(V,599,E)) directlyIncreases kin(p(HGNC:BRAF))'
    # bel2 = 'p(HGNC:BRAF, var("p.599V>E")) directlyIncreases act(p(HGNC:BRAF), ma(kin))'

    bel1 = 'kin(p(HGNC:BRAF))'
    bel2 = 'act(p(HGNC:BRAF), ma(kin))'

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2

    # cat() -> act()
    bel1 = 'cat(p(RGD:Sod1))'
    bel2 = 'act(p(RGD:Sod1), ma(cat))'

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2

    # act() -> act()
    bel1 = 'act(p(RGD:Sod1))'
    bel2 = 'act(p(RGD:Sod1))'

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2

    # sub() -> var()

    # p(HGNC:CFTR, var(p.Gly576Ala))  # substitution using 3 or 1 letter amino acid code, *=stop codon
    # p(HGNC:CFTR, var(p.C65* ))  # truncation at residue 65
    # r(HGNC:CFTR), var(r.243a>u)  # [a, g, c, u]
    # g(HGNC:CFTR), var(c.243A>T)  # [A, G, C, T]  (g.* prefix is for genomic sequence)

    bel1 = 'p(HGNC:PIK3CA, sub(E, 545, K))'
    bel2 = 'p(HGNC:PIK3CA, var("p.Glu545Lys"))'

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2

    # sub()
    bel1 = 'act(p(MGI:Hras, sub(G, 12, V)), ma(gtp)) increases act(complex(SCOMP:\"NADPH Oxidase Complex\"), ma(cat))'
    bel2 = 'act(p(MGI:Hras, var("p.Gly12Val")), ma(gtp)) increases act(complex(SCOMP:\"NADPH Oxidase Complex\"), ma(cat))'

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2

    # trunc() -> var()
    bel1 = 'p(HGNC:ABCA1, trunc(1851))'
    bel2 = 'p(HGNC:ABCA1, var("truncated at 1851"))'

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2

    # fus()
    bel1 = 'r(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626), pmod(P))'
    bel2 = 'r(fus(HGNC:BCR, "r.1_1875", HGNC:JAK2, "r.2626_?"), pmod(Ph))'

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2

    bel1 = 'p(HGNC:BCR, fus(HGNC:JAK2))'
    bel2 = 'p(fus(HGNC:BCR, ?, HGNC:JAK2, ?))'

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2

    # pmod() - updating modtype
    bel1 = 'p(HGNC:MAPK1, pmod(P, Thr, 185))'
    bel2 = 'p(HGNC:MAPK1, pmod(Ph, Thr, 185))'

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2

    # tloc()
    bel1 = 'tloc(p(HGNC:EGFR), MESHCL:Cytoplasm, MESHCL:"Cell Nucleus")'
    bel2 = 'tloc(p(HGNC:EGFR), fromLoc(MESHCL:Cytoplasm), toLoc(MESHCL:"Cell Nucleus"))'

    assert bel.lang.migrate_1_2.migrate(bel1) == bel2


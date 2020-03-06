import bel.lang.belobj
import pytest
from bel.Config import config

bo = bel.lang.belobj.BEL(
    config["bel"]["lang"]["default_bel_version"], config["bel_api"]["servers"]["api_url"]
)


# def test_ortho():

#     gene_species_id_tuples = [('HGNC:A1BG', 'TAX:10090'),
#                               ('HGNC:ROCK1', 'TAX:10090'),
#                               ('HGNC:SOD1', 'TAX:10090'),
#                               ('HGNC:TIMP2', 'TAX:10090')]
#     list_of_expected = [['SP:Q19LI2'],
#                         ['EG:19877'],
#                         ['EG:20655'],
#                         ['MGI:Timp2']]

#     for index, (gene, species) in enumerate(gene_species_id_tuples):
#         result = bo.orthologize(gene, species)
#         assert result == list_of_expected[index]


def test_species():

    assertion = "p(SP:P31749) increases act(p(HGNC:EGF))"
    bo.parse(assertion)
    bo.collect_nsarg_norms()

    print(f"Species should equal TAX:9606 :: {bo.ast.species}")

    correct = set()
    correct.add(("TAX:9606", "human"))

    assert correct == bo.ast.species


def test_multi_species():

    assertion = "p(MGI:Egf) increases act(p(HGNC:EGF))"
    bo.parse(assertion)
    bo.collect_nsarg_norms()

    print(f"Species should be human and mouse:: {bo.ast.species}")

    correct = set()
    correct.add(("TAX:9606", "human"))
    correct.add(("TAX:10090", "mouse"))

    assert correct == bo.ast.species


@pytest.mark.skip(reason="Missing namespace info")
def test_obsolete_term_orthologization():

    assertion = "p(HGNC:FAM46C)"
    correct = "p(MGI:Tent5c)"

    result = bo.parse(assertion).orthologize("TAX:10090").to_string()
    print("Orthologized assertion", result)

    assert correct == result

    # Check species
    correct = set()
    correct.add(("TAX:10090", "mouse"))

    assert correct == bo.ast.species


@pytest.mark.skip(reason="Need to update BEL parsing for this to work")
# BEL parsing should be able to handle naked NSArg strings but can't right now
def test_obsolete_term_NSArg_orthologization():

    assertion = "HGNC:FAM46C"
    correct = "MGI:Tent5c"

    result = bo.parse(assertion).orthologize("TAX:10090").to_string()
    print("Orthologized assertion", result)

    assert correct == result

    # Check species
    correct = set()
    correct.add(("TAX:10090", "mouse"))

    assert correct == bo.ast.species


@pytest.mark.skip(reason="Missing namespace info")
def test_orthologization():
    """Test orthologization of assertion"""

    assertion = "p(SP:P31749) increases act(p(HGNC:EGF))"
    correct = "p(MGI:Akt1) increases act(p(MGI:Egf))"
    result = bo.parse(assertion).orthologize("TAX:10090").to_string()
    print("Orthologized assertion", result)

    assert correct == result

    # Check species
    correct = set()
    correct.add(("TAX:10090", "mouse"))

    assert correct == bo.ast.species


@pytest.mark.skip(reason="Missing namespace info")
def test_multi_orthologization():
    """Test multiple species orthologization of assertion"""

    assertion = "p(MGI:Akt1) increases act(p(HGNC:EGF))"
    correct = "p(MGI:Akt1) increases act(p(MGI:Egf))"
    result = bo.parse(assertion).orthologize("TAX:10090").to_string()
    print("Orthologized assertion", result)

    assert correct == result

    # Check species
    correct = set()
    correct.add(("TAX:10090", "mouse"))

    assert correct == bo.ast.species


@pytest.mark.skip(reason="Missing namespace info")
def test_ortho_one():

    statement = 'act(p(HGNC:AKT1), ma(GO:"kinase activity"))'
    expected = 'activity(proteinAbundance(MGI:Akt1), molecularActivity(GO:"kinase activity"))'

    bo.parse(statement)
    bo.orthologize("TAX:10090")

    print(bo.ast.to_string(fmt="long"))

    assert bo.ast.to_string(fmt="long") == expected


@pytest.mark.skip(reason="Missing namespace info")
def test_ortho_two():

    statement = 'act(p(HGNC:A1BG), ma(GO:"catalytic activity")) directlyIncreases complex(p(HGNC:ROCK1), p(HGNC:SOD1), p(HGNC:TIMP2))'
    expected = 'activity(proteinAbundance(MGI:A1bg), molecularActivity(GO:"catalytic activity")) directlyIncreases complexAbundance(proteinAbundance(MGI:Rock1), proteinAbundance(MGI:Sod1), proteinAbundance(MGI:Timp2))'

    bo.parse(statement)
    bo.orthologize("TAX:10090")
    assert bo.ast.to_string(fmt="long") == expected


@pytest.mark.skip(reason="Missing namespace info")
def test_ortho_nested():

    statement = 'act(p(HGNC:A1BG), ma(GO:"catalytic activity")) directlyIncreases (complex(p(HGNC:ROCK1), p(HGNC:SOD1), p(HGNC:TIMP2)) directlyIncreases complex(p(HGNC:ROCK1), p(HGNC:SOD1), p(HGNC:TIMP2)))'
    expected = 'activity(proteinAbundance(MGI:A1bg), molecularActivity(GO:"catalytic activity")) directlyIncreases (complexAbundance(proteinAbundance(MGI:Rock1), proteinAbundance(MGI:Sod1), proteinAbundance(MGI:Timp2)) directlyIncreases complexAbundance(proteinAbundance(MGI:Rock1), proteinAbundance(MGI:Sod1), proteinAbundance(MGI:Timp2)))'

    bo.parse(statement)
    bo.orthologize("TAX:10090")
    assert bo.ast.to_string(fmt="long") == expected


@pytest.mark.skip(reason="Missing namespace info")
def test_ortho_three():
    statement = "act(p(HGNC:NR1I3))"
    expected = "act(p(MGI:Nr1i3))"

    bo.parse(statement)
    bo.orthologize("TAX:10090")
    assert bo.to_string() == expected


@pytest.mark.skip(reason="Missing namespace info")
def test_ortho_partial():
    # Checking that partially_orthologized attribute is correctly set

    # Fully orthologized
    statement = 'act(p(HGNC:A1BG), ma(GO:"catalytic activity")) directlyIncreases complex(p(SFAM:TEST), p(HGNC:ROCK1), p(HGNC:SOD1), p(HGNC:TIMP2))'
    expected = 'activity(proteinAbundance(MGI:A1bg), molecularActivity(GO:"catalytic activity")) directlyIncreases complexAbundance(proteinAbundance(SFAM:TEST), proteinAbundance(MGI:Rock1), proteinAbundance(MGI:Sod1), proteinAbundance(MGI:Timp2))'

    bo.parse(statement)
    bo.orthologize("TAX:10090")

    print(bo.ast.to_string(fmt="long"))

    assert bo.ast.to_string(fmt="long") == expected
    assert len(bo.ast.species) == 1

    # Partially orthologized p(MGI:Sult2a1) cannot be orthologized
    statement = 'act(p(MGI:A1bg), ma(GO:"catalytic activity")) directlyIncreases complex(p(MGI:Rock1), p(MGI:Sod1), p(MGI:Sult2a1))'
    expected = 'activity(proteinAbundance(HGNC:A1BG), molecularActivity(GO:"catalytic activity")) directlyIncreases complexAbundance(proteinAbundance(HGNC:ROCK1), proteinAbundance(HGNC:SOD1), proteinAbundance(MGI:Sult2a1))'

    bo.parse(statement)
    bo.orthologize("TAX:9606")

    print("Orthologized", bo.ast.to_string(fmt="long"))

    assert bo.ast.to_string(fmt="long") == expected

    print("Species2: ", bo.ast.species)

    assert len(bo.ast.species) > 1

    # Not orthologizable
    statement = "bp(GO:apoptosis)"
    expected = "bp(GO:apoptosis)"

    bo.parse(statement)
    bo.orthologize("TAX:10090")

    print(bo.ast.to_string(fmt="medium"))

    assert bo.ast.to_string(fmt="medium") == expected
    assert len(bo.ast.species) == 0

    # Fully orthologized - check that partially_orthologized attribute is reset
    statement = 'act(p(HGNC:A1BG), ma(GO:"catalytic activity")) directlyIncreases complex(p(HGNC:ROCK1), p(HGNC:SOD1), p(HGNC:TIMP2))'
    expected = 'activity(proteinAbundance(MGI:A1bg), molecularActivity(GO:"catalytic activity")) directlyIncreases complexAbundance(proteinAbundance(MGI:Rock1), proteinAbundance(MGI:Sod1), proteinAbundance(MGI:Timp2))'

    bo.parse(statement)
    print("1 Species", bo.ast.species)
    bo.orthologize("TAX:10090")

    print(bo.ast.to_string(fmt="long"))

    assert bo.ast.to_string(fmt="long") == expected
    print("2 Species", bo.ast.species)
    assert len(bo.ast.species) == 1

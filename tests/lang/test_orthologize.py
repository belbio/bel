import bel.lang.belobj
from bel.Config import config

bo = bel.lang.belobj.BEL(config['bel']['lang']['default_bel_version'], config['bel_api']['servers']['api_url'])


# def test_ortho():

#     gene_species_id_tuples = [('HGNC:A1BG', 'TAX:10090'),
#                               ('HGNC:ROCK1', 'TAX:10090'),
#                               ('HGNC:SOD1', 'TAX:10090'),
#                               ('HGNC:TIMP2', 'TAX:10090')]
#     list_of_expected = [['SP:Q19LI2'],
#                         ['EG:19877'],
#                         ['EG:20655'],
#                         ['EG:21858']]

#     for index, (gene, species) in enumerate(gene_species_id_tuples):
#         result = bo.orthologize(gene, species)
#         assert result == list_of_expected[index]


def test_ortho_one():

    statement = 'act(p(HGNC:AKT1), ma(GO:"kinase activity"))'
    expected = 'activity(proteinAbundance(MGI:Akt1), molecularActivity(GO:"kinase activity"))'

    bo.parse(statement)
    bo.orthologize('TAX:10090')

    print(bo.ast.to_string(fmt='long'))

    assert bo.ast.to_string(fmt='long') == expected


def test_ortho_two():

    statement = 'act(p(HGNC:A1BG), ma(GO:"catalytic activity")) directlyIncreases complex(p(HGNC:ROCK1), p(HGNC:SOD1), p(HGNC:TIMP2))'
    expected = 'activity(proteinAbundance(MGI:A1bg), molecularActivity(GO:"catalytic activity")) directlyIncreases complexAbundance(proteinAbundance(MGI:Rock1), proteinAbundance(MGI:Sod1), proteinAbundance(EG:21858))'

    bo.parse(statement)
    bo.orthologize('TAX:10090')
    assert bo.ast.to_string(fmt='long') == expected


def test_ortho_nested():

    statement = 'act(p(HGNC:A1BG), ma(GO:"catalytic activity")) directlyIncreases (complex(p(HGNC:ROCK1), p(HGNC:SOD1), p(HGNC:TIMP2)) directlyIncreases complex(p(HGNC:ROCK1), p(HGNC:SOD1), p(HGNC:TIMP2)))'
    expected = 'activity(proteinAbundance(MGI:A1bg), molecularActivity(GO:"catalytic activity")) directlyIncreases (complexAbundance(proteinAbundance(MGI:Rock1), proteinAbundance(MGI:Sod1), proteinAbundance(EG:21858)) directlyIncreases complexAbundance(proteinAbundance(MGI:Rock1), proteinAbundance(MGI:Sod1), proteinAbundance(EG:21858)))'

    bo.parse(statement)
    bo.orthologize('TAX:10090')
    assert bo.ast.to_string(fmt='long') == expected


def test_ortho_three():
    statement = 'act(p(HGNC:NR1I3))'
    expected = 'act(p(MGI:Nr1i3))'

    bo.parse(statement)
    bo.orthologize('TAX:10090')
    assert bo.to_string() == expected


def test_ortho_partial():
    # Checking that partially_orthologized attribute is correctly set

    # Fully orthologized
    statement = 'act(p(HGNC:A1BG), ma(GO:"catalytic activity")) directlyIncreases complex(p(SFAM:TEST), p(HGNC:ROCK1), p(HGNC:SOD1), p(HGNC:TIMP2))'
    expected = 'activity(proteinAbundance(MGI:A1bg), molecularActivity(GO:"catalytic activity")) directlyIncreases complexAbundance(proteinAbundance(SFAM:TEST), proteinAbundance(MGI:Rock1), proteinAbundance(MGI:Sod1), proteinAbundance(EG:21858))'

    bo.parse(statement)
    bo.orthologize('TAX:10090')

    print(bo.ast.to_string(fmt='long'))

    assert bo.ast.to_string(fmt='long') == expected
    assert len(bo.ast.species) == 1

    # Partially orthologized p(MGI:Sult2a1) cannot be orthologized
    statement = 'act(p(MGI:A1bg), ma(GO:"catalytic activity")) directlyIncreases complex(p(MGI:Rock1), p(MGI:Sod1), p(MGI:Sult2a1))'
    expected = 'activity(proteinAbundance(HGNC:A1BG), molecularActivity(GO:"catalytic activity")) directlyIncreases complexAbundance(proteinAbundance(HGNC:ROCK1), proteinAbundance(HGNC:SOD1), proteinAbundance(MGI:Sult2a1))'

    bo.parse(statement)
    bo.orthologize('TAX:9606')

    print('Orthologized', bo.ast.to_string(fmt='long'))

    assert bo.ast.to_string(fmt='long') == expected

    print('Species2: ', bo.ast.species)

    assert len(bo.ast.species) > 1

    # Not orthologizable
    statement = 'bp(GO:apoptosis)'
    expected = 'bp(GO:apoptosis)'

    bo.parse(statement)
    bo.orthologize('TAX:10090')

    print(bo.ast.to_string(fmt='medium'))

    assert bo.ast.to_string(fmt='medium') == expected
    assert len(bo.ast.species) == 0

    # Fully orthologized - check that partially_orthologized attribute is reset
    statement = 'act(p(HGNC:A1BG), ma(GO:"catalytic activity")) directlyIncreases complex(p(HGNC:ROCK1), p(HGNC:SOD1), p(HGNC:TIMP2))'
    expected = 'activity(proteinAbundance(MGI:A1bg), molecularActivity(GO:"catalytic activity")) directlyIncreases complexAbundance(proteinAbundance(MGI:Rock1), proteinAbundance(MGI:Sod1), proteinAbundance(EG:21858))'

    bo.parse(statement)
    print('1 Species', bo.ast.species)
    bo.orthologize('TAX:10090')

    print(bo.ast.to_string(fmt='long'))

    assert bo.ast.to_string(fmt='long') == expected
    print('2 Species', bo.ast.species)
    assert len(bo.ast.species) == 1


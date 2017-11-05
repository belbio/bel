import bel_lang
from bel_lang.defaults import defaults

bel_obj = bel_lang.BEL(defaults['bel_version'], defaults['belapi_endpoint'])


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
#         result = bel_obj.orthologize(gene, species)
#         assert result == list_of_expected[index]


def test_ortho_one():

    statement = 'act(p(HGNC:AKT1), ma(GO:"kinase activity"))'
    expected = 'act(p(SP:P31750), ma(GO:"kinase activity"))'

    bel_obj.parse(statement)
    print(bel_obj.ast.bel_subject.to_string())

    bel_obj.orthologize('TAX:10090')
    print(bel_obj.ast.bel_subject.to_string())

    assert bel_obj.ast.to_string() == expected


def test_ortho_two():

    statement = 'act(p(HGNC:A1BG), ma(GO:"catalytic activity")) directlyIncreases complex(p(HGNC:ROCK1), p(HGNC:SOD1), p(HGNC:TIMP2))'
    expected = 'act(p(SP:Q19LI2), ma(GO:"catalytic activity")) directlyIncreases complex(p(EG:19877), p(EG:20655), p(EG:21858))'

    bel_obj.parse(statement)
    print(bel_obj.ast.to_string())
    bel_obj.orthologize('TAX:10090')
    print(bel_obj.ast.to_string())
    assert bel_obj.ast.to_string() == expected

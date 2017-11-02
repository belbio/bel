import bel_lang
import pytest
from bel_lang.exceptions import *

SPECIFIED_VERSION = '2.0.0'
SPECIFIED_ENDPOINT = 'example-endpoint'

B_OBJ = bel_lang.BEL(SPECIFIED_VERSION, SPECIFIED_ENDPOINT)


def test_ortho():

    gene_species_id_tuples = [('HGNC:A1BG', 'TAX:10090'),
                              ('HGNC:ROCK1', 'TAX:10090'),
                              ('HGNC:SOD1', 'TAX:10090'),
                              ('HGNC:TIMP2', 'TAX:10090')]
    list_of_expected = [['SP:Q19LI2'],
                        ['EG:19877'],
                        ['EG:20655'],
                        ['EG:21858']]

    for index, (gene, species) in enumerate(gene_species_id_tuples):
        result = B_OBJ.orthologize(gene, species)
        assert result == list_of_expected[index]

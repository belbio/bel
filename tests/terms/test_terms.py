import bel.terms.terms


def test_terms():

    term_id = 'SP:P31749'
    check = {'canonical': 'EG:207', 'decanonical': 'HGNC:AKT1', 'original': 'SP:P31749'}

    result = bel.terms.terms.get_normalized_terms(term_id)

    assert check == result

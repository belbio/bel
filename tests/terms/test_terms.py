# Local Imports
import bel.terms.terms


def test_terms():

    term_id = "SP:P31749"
    check = {"canonical": "EG:207", "decanonical": "HGNC:AKT1", "original": "SP:P31749"}

    result = bel.terms.terms.get_normalized_terms(term_id)

    assert check == result


def test_obsolete_term():

    term_id = "HGNC:FAM46C"

    check_id = "HGNC:TENT5C"

    result = bel.terms.terms.get_terms(term_id)

    print("Result", result)

    assert check_id == result[0]["id"]

    result = bel.terms.terms.get_normalized_terms(term_id)

    print("Result", result)

    check = {"canonical": "EG:54855", "decanonical": "HGNC:TENT5C", "original": "HGNC:FAM46C"}

    assert check == result

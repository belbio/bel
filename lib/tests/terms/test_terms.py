# Local Imports
import bel.schemas
import bel.terms.terms
import pytest


@pytest.mark.parametrize("test_key, expected", [("HGNC:AKT1", "HGNC:391")])
def test_get_terms(test_key, expected):

    results = bel.terms.terms.get_terms(test_key)

    print("Results", results)

    assert results[0].key == expected


def test_equivalents():
    term_key = "HGNC:AKT1"

    expected = {
        "equivalents": [
            {"term_key": "HGNC:AKT1", "namespace": "HGNC", "primary": None},
            {"term_key": "SP:P31749", "namespace": "SP", "primary": True},
            {"term_key": "uniprot:P31749", "namespace": "uniprot", "primary": None},
            {"term_key": "refseq:NM_005163", "namespace": "refseq", "primary": None},
            {"term_key": "ensembl:ENSG00000142208", "namespace": "ensembl", "primary": None},
            {"term_key": "orphanet:281472", "namespace": "orphanet", "primary": None},
            {"term_key": "EG:207", "namespace": "EG", "primary": True},
            {"term_key": "SP:AKT1_HUMAN", "namespace": "SP", "primary": None},
        ]
    }

    results = bel.terms.terms.get_equivalents(term_key)

    print("Results", results)

    assert results == expected


def test_get_normalized_terms():

    term_key = "SP:P31749"

    expected = {
        "normalized": "SP:P31749",
        "canonical": "EG:207",
        "decanonical": "HGNC:391",
        "original": "SP:P31749",
    }

    results = bel.terms.terms.get_normalized_terms(term_key)

    print("Terms", results)

    assert results == expected


def test_obsolete_term():

    term_key = "HGNC:FAM46C"

    expected = "HGNC:24712"  # label=TENT5C

    result_key = bel.terms.terms.get_term(term_key).key

    print("Term Result", result_key, "\n\n")

    assert expected == result_key

    results = bel.terms.terms.get_normalized_terms(term_key)

    print("Normalized Results", results)

    expected = {
        "original": "HGNC:FAM46C",
        "normalized": "HGNC:24712",
        "canonical": "EG:54855",
        "decanonical": "HGNC:24712",
    }

    assert results == expected


def test_obsolete_equivalencing():
    """Check PBX2 equivalencing

    HGNC:PBX2 matches these term_keys: ['HGNC:PBX2', 'HGNC:PBX2P1']"] - it is an obsolete term for PBX2P1
    """

    term_key = "HGNC:PBX2"

    expected = {
        "equivalents": [
            {"term_key": "HGNC:PBX2", "namespace": "HGNC", "primary": None},
            {"term_key": "SP:P40425", "namespace": "SP", "primary": True},
            {"term_key": "uniprot:P40425", "namespace": "uniprot", "primary": None},
            {"term_key": "refseq:NM_002586", "namespace": "refseq", "primary": None},
            {"term_key": "ensembl:ENSG00000204304", "namespace": "ensembl", "primary": None},
            {"term_key": "EG:5089", "namespace": "EG", "primary": True},
            {"term_key": "SP:PBX2_HUMAN", "namespace": "SP", "primary": None},
        ]
    }

    results = bel.terms.terms.get_equivalents(term_key)

    import json

    print("Results:\n", json.dumps(results, indent=4))

    assert results == expected


def test_collapsed_terms():
    """Terms collapsed together due to Swissprot
    
    HGNC:IFNA1 and HGNC:IFNA13 - get collapsed together due to their SP entry - https://www.uniprot.org/uniprot/P01562

    HGNC:DEFB4A and HGNC:DEFB4B - get collapsed together due to their SP entry - https://www.uniprot.org/uniprot/O15263
    """

    term_key = "HGNC:IFNA1"
    expected = {
        "normalized": "HGNC:5417",
        "original": "HGNC:IFNA1",
        "canonical": "EG:3439",
        "decanonical": "HGNC:5417",
    }

    results = bel.terms.terms.get_normalized_terms(term_key)
    print(f"Results {term_key}", results)

    assert results == expected

    term_key = "HGNC:IFNA13"
    expected = {
        "normalized": "HGNC:5419",
        "original": "HGNC:IFNA13",
        "canonical": "EG:3447",
        "decanonical": "HGNC:5419",
    }

    results = bel.terms.terms.get_normalized_terms(term_key)
    print(f"Results {term_key}", results)

    assert results == expected

    term_key = "HGNC:DEFB4A"
    expected = {
        "normalized": "HGNC:2767",
        "original": "HGNC:DEFB4A",
        "canonical": "EG:1673",
        "decanonical": "HGNC:2767",
    }

    results = bel.terms.terms.get_normalized_terms(term_key)
    print(f"Results {term_key}", results)

    assert results == expected

    term_key = "HGNC:DEFB4B"
    expected = {
        "normalized": "HGNC:30193",
        "original": "HGNC:DEFB4B",
        "canonical": "EG:100289462",
        "decanonical": "HGNC:30193",
    }

    results = bel.terms.terms.get_normalized_terms(term_key)
    print(f"Results {term_key}", results)

    assert results == expected

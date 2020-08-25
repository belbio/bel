# Local Imports
# Standard Library
import json

import bel.core.settings as settings
import bel.edge.edges
import pytest
from bel.schemas.bel import AssertionStr

bel_version = "latest"


def test_problem_terms_nested():
    """Bad canonicalization for nested statements
    
    There are issues with the canonicalization and decanonicalization of these terms:
        complex(p(HGNC:IFNA1), p(HGNC:IFNA13), p(HGNC:DEFB4A), p(HGNC:DEFB4B))

    HGNC:IFNA1 and HGNC:IFNA13 - get collapsed together due to their SP entry - https://www.uniprot.org/uniprot/P01562

    HGNC:DEFB4A and HGNC:DEFB4B - get collapsed together due to their SP entry - https://www.uniprot.org/uniprot/O15263
    
    At the very least, the normalization function should be consistent in how it normalizes/canonicalizes these terms.
    """

    orthologize_targets = ["TAX:9606", "TAX:10090"]

    assertions = [
        AssertionStr(
            entire="complex(p(HGNC:IFNA1), p(HGNC:IFNA13), p(HGNC:DEFB4A), p(HGNC:DEFB4B)) increases (p(HGNC:EGF) increases complex(p(HGNC:IFNA1), p(HGNC:IFNA13), p(HGNC:DEFB4A), p(HGNC:DEFB4B)))"
        )
    ]

    expected = False

    results = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version,
    )
    print("Results", results)

    assert results == expected


# TODO - remove any computed orthologized edges that are species=None
def test_assertion_edge_info_dup_computed():
    """Do not allow computed edges to be created that are duplicates of the original edge or orig/orthologized edge"""

    orthologize_targets = ["TAX:9606", "TAX:10090"]

    assertions = [AssertionStr(entire="complex(p(HGNC:EGF)) hasComponent p(HGNC:EGF)")]

    expected = {
        "edge_info_list": [
            {
                "edge_types": ["computed"],
                "species_id": "None",
                "species_label": "None",
                "canonical": {
                    "subject": "complex(p(HGNC:EGF))",
                    "relation": "hasComponent",
                    "object": "p(HGNC:EGF)",
                },
                "decanonical": {
                    "subject": "complex(p(HGNC:EGF))",
                    "relation": "hasComponent",
                    "object": "p(HGNC:EGF)",
                },
                "subject_comp": ["p(HGNC:EGF)", "HGNC:EGF"],
                "object_comp": ["HGNC:EGF"],
                "errors": [],
            }
        ]
    }

    nanopub_type = ""  # e.g. not backbone which would skip orthologization

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_1():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    assertions = [
        AssertionStr(subject="act(p(HGNC:DUOX1))", relation="decreases", object="act(p(HGNC:SRC))")
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_2():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    assertions = [
        AssertionStr(subject="act(p(MGI:Nr1i2))", relation="increases", object="r(MGI:Cyp3a11)")
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_3():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    assertions = [
        AssertionStr(
            subject="act(p(MGI:Abcc10))",
            relation="association",
            object='act(p(PMIPFAM:"ABCC subfamily transporter"))',
        )
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_4():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    assertions = [
        AssertionStr(subject="act(p(MGI:Hnf4a))", relation="decreases", object="r(MGI:AhR)")
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_5():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    assertions = [
        AssertionStr(
            subject='path(TBD:"Neuropathic Pain")',
            relation="positiveCorrelation",
            object="p(HGNC:IL6)",
        )
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_6():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    assertions = [
        AssertionStr(subject="p(HGNC:AKT1)", relation="increases", object="act(p(HGNC:EGF))")
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_7():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    assertions = [
        AssertionStr(
            subject="complex(p(HGNC:AKT1), p(HGNC:EGF))",
            relation="increases",
            object="bp(GO:apoptosis)",
        )
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_8():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    assertions = [
        AssertionStr(subject="complex(p(HGNC:AKT2), p(HGNC:EGF))", relation="", object="")
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_9():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    # Bad assertion - extra parenthesis in object
    assertions = [
        AssertionStr(
            subject="complex(p(HGNC:AKT2), p(HGNC:EGF))",
            relation="increases",
            object="bp(GO:apoptosis))",
        )
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_10():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    # MGI:Sult2a1 doesn't have an ortholog
    assertions = [
        AssertionStr(subject="act(p(MGI:Akt1))", relation="decreases", object="r(MGI:Sult2a1)")
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_11():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    assertions = [
        AssertionStr(subject="act(p(MGI:Rora))", relation="decreases", object="r(MGI:Egf)")
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result


def test_generate_assertion_edge_info_12():
    """Set of assertions to test for creating edges"""

    nanopub_type = ""  # e.g. not backbone which would skip orthologization
    orthologize_targets = ["TAX:9606", "TAX:10090"]

    # RGD:Birc3 - no orthologs in EntrezGene
    assertions = [
        AssertionStr(
            subject='a(SCHEM:"Smoke, cigarette")', relation="decreases", object="p(RGD:Birc3)"
        )
    ]

    expected = {}

    result = bel.edge.edges.generate_assertion_edge_info(
        assertions, orthologize_targets, bel_version, nanopub_type
    )

    print("Result:\n", json.dumps(result, indent=4))

    assert expected == result

# Third Party
import pytest

# Local
import bel.schemas
import bel.terms.orthologs


def test_orthologs():
    """Get orthologs"""

    term_key = "HGNC:AKT1"

    expected = {
        "TAX:9606": "EG:207",
        "TAX:10116": "EG:24185",
        "TAX:7955": "EG:101910198",
        "TAX:10090": "EG:11651",
    }

    orthologs = bel.terms.orthologs.get_orthologs(term_key)

    # Standard Library
    import json

    print("Orthologs:\n", json.dumps(orthologs, indent=4))

    assert orthologs == expected

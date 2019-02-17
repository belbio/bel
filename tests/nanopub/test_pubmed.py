import bel.nanopub.pubmed
import json


def test_get_pubmed():
    """Get a normal Pubmed record"""

    pmid = '10551823'

    doc = bel.nanopub.pubmed.get_pubmed(pmid)

    print('Doc:\n', json.dumps(doc, indent=4))

    assert doc['pmid'] == pmid


def test_get_pubmed_structured_abstract():
    """Make sure we collect full structured abstract

    Structured abstracts are stored differently than regular abstracts
    """

    pmid = '30562878'

    doc = bel.nanopub.pubmed.get_pubmed(pmid)

    print('Doc:\n', json.dumps(doc, indent=4))

    assert doc['pmid'] == pmid
    assert "Subjects and Methods" in doc['abstract']

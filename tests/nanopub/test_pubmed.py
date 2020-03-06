import json
import time

import bel.nanopub.pubmed


def test_get_pubmed1():
    """Get a normal Pubmed record"""

    pmid = "10551823"

    doc = bel.nanopub.pubmed.get_pubmed(pmid)

    print("Doc:\n", json.dumps(doc, indent=4))

    assert doc["pmid"] == pmid


def test_get_pubmed2():
    """Get a normal Pubmed record"""

    # TODO https://stackoverflow.com/questions/4770191/lxml-etree-element-text-doesnt-return-the-entire-text-from-an-element
    #  https://www.ncbi.nlm.nih.gov/pubmed/?term=27822475&report=xml&format=text
    #   <Abstract>
    #     <AbstractText>Rheumatoid arthritis (RA) appears as inflammation of synovial tissue and joint destruction. Receptor activator of NF-<i>κ</i>B (RANK) is a member of the TNF receptor superfamily and a receptor for the RANK ligand (RANKL). In this study, we examined the expression of RANK<sup>high</sup> and CCR6 on CD14<sup>+</sup> monocytes from patients with RA and healthy volunteers. Peripheral blood samples were obtained from both the RA patients and the healthy volunteers. Osteoclastogenesis from monocytes was induced by RANKL and M-CSF <i>in vitro</i>. To study the expression of RANK<sup>high</sup> and CCR6 on CD14<sup>+</sup> monocytes, two-color flow cytometry was performed. Levels of expression of RANK on monocytes were significantly correlated with the level of osteoclastogenesis in the healthy volunteers. The expression of RANK<sup>high</sup> on CD14<sup>+</sup> monocyte in RA patients without treatment was elevated and that in those receiving treatment was decreased. In addition, the high-level expression of RANK on CD14<sup>+</sup> monocytes was correlated with the high-level expression of CCR6 in healthy volunteers. Monocytes expressing both RANK and CCR6 differentiate into osteoclasts. The expression of CD14<sup>+</sup>RANK<sup>high</sup> in untreated RA patients was elevated. RANK and CCR6 expressed on monocytes may be novel targets for the regulation of bone resorption in RA and osteoporosis.</AbstractText>
    #   </Abstract>
    #   stops abstract at first subtag  ...NF-<i>
    #
    pmid = "27822475"

    doc = bel.nanopub.pubmed.get_pubmed(pmid)

    print("Doc:\n", json.dumps(doc, indent=4))

    assert doc["pmid"] == pmid
    assert (
        doc["abstract"]
        == "Rheumatoid arthritis (RA) appears as inflammation of synovial tissue and joint destruction. Receptor activator of NF-B (RANK) is a member of the TNF receptor superfamily and a receptor for the RANK ligand (RANKL). In this study, we examined the expression of RANK and CCR6 on CD14 monocytes from patients with RA and healthy volunteers. Peripheral blood samples were obtained from both the RA patients and the healthy volunteers. Osteoclastogenesis from monocytes was induced by RANKL and M-CSF . To study the expression of RANK and CCR6 on CD14 monocytes, two-color flow cytometry was performed. Levels of expression of RANK on monocytes were significantly correlated with the level of osteoclastogenesis in the healthy volunteers. The expression of RANK on CD14 monocyte in RA patients without treatment was elevated and that in those receiving treatment was decreased. In addition, the high-level expression of RANK on CD14 monocytes was correlated with the high-level expression of CCR6 in healthy volunteers. Monocytes expressing both RANK and CCR6 differentiate into osteoclasts. The expression of CD14RANK in untreated RA patients was elevated. RANK and CCR6 expressed on monocytes may be novel targets for the regulation of bone resorption in RA and osteoporosis."
    )
    time.sleep(1)


def test_get_pubmed3():
    """Get a book Pubmed record"""

    pmid = "28520369"

    doc = bel.nanopub.pubmed.get_pubmed(pmid)

    print("Doc:\n", json.dumps(doc, indent=4))

    assert doc["pmid"] == pmid
    assert doc["title"] == "Medical Genetics Summaries"
    assert doc["pub_date"] == "2012-01-01"


def test_get_pubmed4():
    """Get a bad date Pubmed record"""

    pmid = "24656623"

    doc = bel.nanopub.pubmed.get_pubmed(pmid)

    print("Doc:\n", json.dumps(doc, indent=4))

    assert doc["pmid"] == pmid
    assert doc["pub_date"] == "2015-01-01"

    time.sleep(1)


def test_get_pubmed_structured_abstract():
    """Make sure we collect full structured abstract

    Structured abstracts are stored differently than regular abstracts
    """

    pmid = "30562878"

    doc = bel.nanopub.pubmed.get_pubmed(pmid)

    print("Doc:\n", json.dumps(doc, indent=4))

    assert doc["pmid"] == pmid
    assert "SUBJECT AND METHODS" in doc["abstract"]

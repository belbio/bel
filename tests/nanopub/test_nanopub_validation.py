
# Standard Library
import json

# Local Imports
import bel.nanopub.validate
import pytest


# @pytest.mark.skip(reason="Not finished with this test")
def test_validate_nanopub():

    nanopub = {
        "_key": "01DZZ0WBHER1B3MXW2TFDA2QWE",
        "nanopub": {
            "annotations": [{"id": "TAX:9606", "label": "human", "type": "Species"}],
            "assertions": [
                {
                    "object": "act(p(SPX:AKT1_HUMAN)",
                    "relation": "increases",
                    "subject": "act(p(SP:AKT1_HUMAN), ma))",
                }
            ],
            "citation": {
                "abstract": "Recently, we identified the two myeloid related protein-8 (MRP8) (S100A8) and MRP14 (S100A9) as fatty acid-binding proteins (Klempt, M., Melkonyan, H., Nacken, W., Wiesmann, D., Holtkemper, U., and Sorg, C. (1997) FEBS Lett. 408, 81-84). Here we present data that the S100A8/A9 protein complex represents the exclusive arachidonic acid-binding proteins in human neutrophils. Binding and competition studies revealed evidence that (i) fatty acid binding was dependent on the calcium concentration; (ii) fatty acid binding was specific for the protein complex formed by S100A8 and S100A9, whereas the individual components were unable to bind fatty acids; (iii) exclusively polyunsaturated fatty acids were bound by S100A8/A9, whereas saturated (palmitic acid, stearic acid) and monounsaturated fatty acids (oleic acid) as well as arachidonic acid-derived eicosanoids (15-hydroxyeicosatetraenoic acid, prostaglandin E(2), thromboxane B(2), leukotriene B(4)) were poor competitors. Stimulation of neutrophil-like HL-60 cells with phorbol 12-myristate 13-acetate led to the secretion of S100A8/A9 protein complex, which carried the released arachidonic acid. When elevation of intracellular calcium level was induced by A23187, release of arachidonic acid occurred without secretion of S100A8/A9. In view of the unusual abundance in neutrophilic cytosol (approximately 40% of cytosolic protein) our findings assign an important role for S100A8/A9 as mediator between calcium signaling and arachidonic acid effects. Further investigations have to explore the exact function of the S100A8/A9-arachidonic acid complex both inside and outside of neutrophils.",
                "authors": ["Kerkhoff, C", "Klempt, M", "Kaever, V", "Sorg, C"],
                "database": {"id": "10551823", "name": "PubMed"},
                "date_published": "1999-11-12",
                "source_name": "The Journal of biological chemistry",
                "title": "The two calcium-binding proteins, S100A8 and S100A9, are involved in the metabolism of arachidonic acid in human neutrophils.",
            },
            "evidence": "we identified the two myeloid related protein-8 (MRP8) (S100A8) and MRP14 (S100A9) as fatty acid-binding proteins",
            "id": "01DZZ0WBHER1B3MXW2TFDA2QWE",
            "metadata": {
                "gd_createTS": "2020-02-01T00:02:19.634Z",
                "gd_hash": "b9b868e675bdd8ab",
                "gd_internal_comments": "",
                "gd_rev": "_Z92MJja---",
                "gd_status": "draft",
                "gd_updateTS": "2020-02-01T00:02:19.634Z"
            },
            "schema_uri": "https://raw.githubusercontent.com/graphdati/schemas/master/nanopub_graphdati-1.0.0.json",
            "type": {"name": "BEL", "version": "2.1.1"},
        },
        "owners": ["auth0|5b0ec2d2157859716f2b2449"],
    }

    nanopub = bel.nanopub.validate.validate(nanopub, validation_level="force")


    print('DumpVar:\n', json.dumps(nanopub, indent=4))

    assert any([error for assertion in nanopub["nanopub"]["assertions"] for error in assertion["validation"]["errors"] if error["msg"] == "Too many close parentheses at index 25"])
    
    assert any([error for assertion in nanopub["nanopub"]["assertions"] for error in assertion["validation"]["errors"] if error["msg"] == "No matching close parenthesis to open parenthesis at index 40"])

    assert any([error for assertion in nanopub["nanopub"]["assertions"] for error in assertion["validation"]["errors"] if error["msg"] == "Invalid BEL Assertion function act(p(SP:AKT1_HUMAN), ma) - problem with function signatures: Missing position_dependent arguments for activity signature: 0"])

    assert any([warning for assertion in nanopub["nanopub"]["assertions"] for warning in assertion["validation"]["warnings"] if warning["msg"] == "Invalid Term - Assertion term SPX:AKT1_HUMAN allowable entity types: ['Protein'] do not match API term entity types: []"])
